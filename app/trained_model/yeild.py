import os
import pandas as pd
import joblib

from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestRegressor

MODEL_FILE = "yield_model.pkl"
PIPELINE_FILE = "yeild_pipeline.pkl"

if not os.path.exists(MODEL_FILE):

    data = pd.read_csv("final_yeild_dataset.csv")

    # Fix spelling
    data.rename(columns={"yeild": "yield"}, inplace=True)

    # Stratification column
    data["temp"] = pd.cut(
        data["Temperature"],
        bins=[0, 10, 20, 30, 40, 50],
        labels=[1, 2, 3, 4, 5]
    )

    split = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)

    for train_idx, test_idx in split.split(data, data["temp"]):
        train_set = data.iloc[train_idx].drop("temp", axis=1)
        test_set = data.iloc[test_idx].drop("temp", axis=1)

    test_set.to_csv("input.csv", index=False)

    X_train = train_set.drop("yield", axis=1)
    y_train = train_set["yield"]

    # Separate columns
    num_cols = ["Area", "Fertilizer", "Temperature", "rainfall"]
    cat_cols = ["Crop", "Season"]

    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])

    full_pipeline = ColumnTransformer([
        ("num", num_pipeline, num_cols),
        ("cat", cat_pipeline, cat_cols)
    ])

    X_train_prepared = full_pipeline.fit_transform(X_train)

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )

    model.fit(X_train_prepared, y_train)

    print("✅ Model trained successfully")

    joblib.dump(full_pipeline, PIPELINE_FILE)
    joblib.dump(model, MODEL_FILE)

else:
    model = joblib.load(MODEL_FILE)
    pipeline = joblib.load(PIPELINE_FILE)

    input_data = pd.read_csv("input.csv")

    X = input_data.drop("yield", axis=1, errors="ignore")
    X_prepared = pipeline.transform(X)

    predictions = model.predict(X_prepared)

    input_data["predicted_yield"] = predictions
    input_data.to_csv("output.csv", index=False)

    print("✅ Prediction saved in output.csv")