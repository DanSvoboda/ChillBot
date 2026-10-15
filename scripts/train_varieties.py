import torch
from mcp_servers.variety_classifier.model import variety_model
import mcp_servers.variety_classifier.model as classifier_model
from huggingface_hub import HfApi
 
def train(model, train_loader, criterion, optimizer, device):
    print("Starting training...")
    model.train()
    model.to(device)
    running_loss = 0.0
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * inputs.size(0)
    epoch_loss = running_loss / len(train_loader.dataset)
    print(f"Training loss: {epoch_loss:.4f}")
    return epoch_loss
    
def evaluate(model, test_loader, criterion, device):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            test_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data)
    test_loss /= len(test_loader.dataset)
    accuracy = correct.double() / len(test_loader.dataset)
    print(f"Test loss: {test_loss:.4f}, Accuracy: {accuracy:.2%}")
    return test_loss, accuracy

def save_model(model, optimizer, epoch, accuracy, path=classifier_model.PATH_VARIETY_MODEL):
    torch.save({
        "epoch": epoch,
        "model": model.model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "classes": model.classes,
        "accuracy": accuracy,
    }, path)
    print(f"Model saved to {path}")

if __name__ == "__main__":
    model = variety_model()
    if False:  # Set to True if you want to train the model
        for epoch in range(10):
            train_loss = train(model, model.train_loader, model.criterion, model.optimizer, model.device)
            test_loss, accuracy = evaluate(model, model.test_loader, model.criterion, model.device)
            print(f"Epoch [{epoch + 1}/10], Train Loss: {train_loss:.4f}, Test Loss: {test_loss:.4f}, Accuracy: {accuracy:.2%}")
            save_model(model, model.optimizer, epoch, accuracy)    
       
        api = HfApi()
        api.create_repo("DanSvobodaVSE/chillbot-varieties", repo_type="model", exist_ok=True)
        api.upload_file(
            path_or_fileobj="models/varieties/checkpoint.pt",
            path_in_repo="checkpoint.pt",
            repo_id="DanSvobodaVSE/chillbot-varieties",
        )

            

