from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, balanced_accuracy_score
import matplotlib.pyplot as plt
import joblib
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PRODUCTION_DATA_PATH = Path(os.environ["PRODUCTION_DATA_PATH"])
PRODUCTION_MODEL_PATH = Path(os.environ["PRODUCTION_MODEL_PATH"])


NUM = [
    "year",
    # plocha letos je znama pri setbe; yield letos NE (area * yield = production -> leak)
    "area_harvested",
    "area_harvested_change_this_year",
    "climate_value_standard_deviation",
    "climate_value_temperature_change",
    "price_value",
    "yield_prev_year",
    "area_harvested_prev_year",
    "production_prev_year",
    "price_value_prev_year",
    "climate_value_standard_deviation_prev_year",
    "climate_value_temperature_change_prev_year",
    # trend za minuly rok (log-pomer t-1 / t-2)
    "production_change_prev_year",
    "yield_change_prev_year",
    "area_harvested_change_prev_year",
    "price_value_change_prev_year",
    "production_flat_prev_year",
    "production_rose_prev_year",
    "production_abs_change_prev_year",
]

CAT = [
    "area",
    "peppers",
    "climate_flag_standard_deviation",
    "climate_flag_temperature_change",
    "price_flag",
    "flag_prod_prev_year",
]

models = {
    "Dummy": (DummyClassifier(strategy="prior"), {}),
    "LogReg": (LogisticRegression(max_iter=2000, class_weight="balanced"),
               {"clf__C": [0.001, 0.01, 0.1, 1, 10]}),
    "RandomForest": (RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1, class_weight="balanced"),
                     {"clf__max_depth": [3, 6, None],
                      "clf__min_samples_leaf": [10, 30, 100]}),
     "SVC": (SVC(kernel="rbf", class_weight="balanced"),
                {"clf__C": [0.1, 1, 10]}),
}

df = pd.read_csv(PRODUCTION_DATA_PATH)

X_train = df[df["year"] < 2020].drop(columns=["production_rise"])
y_train = df[df["year"] < 2020]["production_rise"]

X_test = df[df["year"] >= 2020].drop(columns=["production_rise"])
y_test = df[df["year"] >= 2020]["production_rise"]   

prep = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                      ("sc", StandardScaler())]), NUM),
    ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
])

for model_name, (model, params) in models.items():
    pipe = Pipeline([
        ("prep", prep),
        ("clf", model),
    ])

    search = GridSearchCV(
        pipe,
        param_grid=params,
        cv=5,
        # accuracy odmenuje konstantni predikci majority (61 % "rise"); ROC AUC meri, jestli model umi radit
        scoring="roc_auc",
        refit=True,
    )
    search.fit(X_train, y_train)
    test_auc = search.score(X_test, y_test)
    y_pred = search.predict(X_test)

    print(f"{model_name} Best CV ROC AUC: {search.best_score_:.4f}")
    print(f"{model_name} Best Parameters: {search.best_params_}")
    print(f"{model_name} Test ROC AUC: {test_auc:.4f}")
    print(f"{model_name} Test Balanced Accuracy: {balanced_accuracy_score(y_test, y_pred):.4f}")
    print(f"{model_name} Test Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    
"""
Dummy Best CV Accuracy: 0.5450
Dummy Best Parameters: {}
Dummy Test Accuracy: 0.5378
LogReg Best CV Accuracy: 0.6999
LogReg Best Parameters: {'clf__C': 10}
LogReg Test Accuracy: 0.8074
RandomForest Best CV Accuracy: 0.5484
RandomForest Best Parameters: {'clf__max_depth': None, 'clf__min_samples_leaf': 10}
RandomForest Test Accuracy: 0.6006
SVC Best CV Accuracy: 0.6274
SVC Best Parameters: {'clf__C': 10}
SVC Test Accuracy: 0.6933
"""
# ^ vysledky se starymi (leaky) featurami - po pretrenovani prepsat a znovu vybrat model
# volím LogReg
pipeline = Pipeline([
    ("prep", prep),
    ("clf", LogisticRegression(max_iter=2000, C=10, class_weight="balanced")),
])
pipeline.fit(X_train, y_train)
pipeline.score(X_test, y_test)



r = permutation_importance(
    pipeline, X_train, y_train,
    scoring="roc_auc", n_repeats=20, random_state=42, n_jobs=-1,
)

imp = (pd.DataFrame({"feature": X_train.columns,
                     "mean": r.importances_mean,
                     "std": r.importances_std})
       .sort_values("mean"))

plt.barh(imp["feature"], imp["mean"], xerr=imp["std"])
plt.xlabel("pokles ROC AUC po zamíchání sloupce")
plt.title("Permutation importance")
plt.tight_layout(); plt.show()

joblib.dump(pipeline, PRODUCTION_MODEL_PATH)