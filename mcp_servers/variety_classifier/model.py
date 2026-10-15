import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms, datasets, models
from huggingface_hub import hf_hub_download

PATH_VARIETY_MODEL = "models/varieties/checkpoint.pt"
PATH_TRAINING_DATA = "data/training/varieties/train"
PATH_TESTING_DATA = "data/training/varieties/test"

class variety_model(nn.Module):
    def __init__(self, load_data=True):
        super(variety_model, self).__init__()

        self.TF_MEAN = [0.485, 0.456, 0.406]
        self.TF_STD = [0.229, 0.224, 0.225]

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        print(f"Using device: {self.device}")

        self.train_tf = transforms.Compose([
                transforms.RandomResizedCrop(224),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize(mean=self.TF_MEAN, std=self.TF_STD)
            ])

        self.test_tf = transforms.Compose([
            transforms.Resize(224),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=self.TF_MEAN, std=self.TF_STD)
        ])

        # Read the checkpoint once (if it exists) - it contains weights AND class names
        checkpoint = None
        if os.path.exists(PATH_VARIETY_MODEL):
            checkpoint = torch.load(PATH_VARIETY_MODEL, map_location=self.device)
        else:
            print(f"No trained model found at {PATH_VARIETY_MODEL}. Please run the training script first.")
            path = hf_hub_download(
                repo_id="DanSvobodaVSE/chillbot-varieties",
                filename="checkpoint.pt",
                local_dir=PATH_VARIETY_MODEL,
            )

        # Training needs the datasets; the server only needs class names
        if load_data:
            self.train_loader, self.train_dataset = self.dataloaders(PATH_TRAINING_DATA, self.train_tf, shuffle=True)
            self.test_loader, self.test_dataset = self.dataloaders(PATH_TESTING_DATA, self.test_tf, shuffle=False)
            self.classes = self.train_dataset.classes
            print(f"Number of training samples: {len(self.train_dataset)}")
        elif checkpoint is not None:
            self.classes = checkpoint["classes"]
        else:
            raise FileNotFoundError(f"No trained model at {PATH_VARIETY_MODEL}. Run the training script first.")
        print(f"Number of classes: {len(self.classes)}")

        self.model = self.build_model(pretrained=checkpoint is None).to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-4)
        self.criterion = nn.CrossEntropyLoss()

        self.trained = checkpoint is not None
        if checkpoint is not None:
            # load_state_dict works IN PLACE - don't assign its return value
            self.model.load_state_dict(checkpoint["model"])
            if "optimizer" in checkpoint:
                self.optimizer.load_state_dict(checkpoint["optimizer"])
            print(f"Loaded model from {PATH_VARIETY_MODEL}")
        else:
            print("Initialized new ResNet18 model.")
            print("Model needs to be trained. Please run the training script.")

    def dataloaders(self, dir, tf, shuffle):
        dataset = datasets.ImageFolder(root=dir, transform=tf)
        loader = DataLoader(dataset, batch_size=32, shuffle=shuffle)
        return loader, dataset

    def build_model(self, pretrained):
        
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        model = models.resnet18(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, len(self.classes))
        return model

    def get_classes(self):
        return self.classes

    def forward(self, x):
        return self.model(x)

    @torch.inference_mode()
    def predict(self, image, top_k=3):
        """Takes a PIL RGB image, returns [(class_name, probability), ...]"""
        self.model.eval()
        x = self.test_tf(image).unsqueeze(0).to(self.device)   # [3,224,224] -> [1,3,224,224]
        probs = torch.softmax(self.model(x), dim=1)[0]
        top = torch.topk(probs, top_k)
        return [(self.classes[i], p) for p, i in zip(top.values.tolist(), top.indices.tolist())]

