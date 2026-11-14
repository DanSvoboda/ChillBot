from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.svm import SVC
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import GridSearchCV
import joblib

import pandas as pd


NUM = [
    "year",
    "area_harvested",
    "production",
    "yield",
    "climate_value_standard_deviation",
    "climate_value_temperature_change",
    "price_value",
    "yield_prev_year",
    "price_value_prev_year",
    "climate_value_standard_deviation_prev_year",
    "climate_value_temperature_change_prev_year",
]

CAT = [
    "flag_prod",
    "flag_prod_desc",
    "area",
    "peppers",
    "climate_flag_standard_deviation",
    "climate_flag_temperature_change",
    "climate_flag_desc_standard_deviation",
    "climate_flag_desc_temperature_change",
    "price_element",
    "price_flag",
    "price_flag_desc",
]

models = {
    "Dummy": (DummyClassifier(strategy="prior"), {}),
    "LogReg": (LogisticRegression(max_iter=2000),
               {"clf__C": [0.001, 0.01, 0.1, 1, 10]}),
    "RandomForest": (RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1),
                     {"clf__max_depth": [3, 6, None],
                      "clf__min_samples_leaf": [10, 30, 100]}),
     "SVC": (SVC(kernel="rbf"),
                {"clf__C": [0.1, 1, 10]}),
}

df = pd.read_csv("data/training/production/papriky-production.csv")

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
        scoring="accuracy",
        refit=True,
    )
    search.fit(X_train, y_train)
    result = search.score(X_test, y_test)
      
    
    print(f"{model_name} Best CV Accuracy: {search.best_score_:.4f}")
    print(f"{model_name} Best Parameters: {search.best_params_}")
    print(f"{model_name} Test Accuracy: {result:.4f}")
    
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
# volím LogReg
pipeline = Pipeline([
    ("prep", prep),
    ("clf", LogisticRegression(max_iter=2000, C=10)),
])
pipeline.fit(X_train, y_train)
pipeline.score(X_test, y_test)

joblib.dump(pipeline, "models/production_clf.pkl")