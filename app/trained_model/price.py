import os
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor

MODEL_FILE = "price_model.pkl"
PIPELINE_FILE = "price_pipeline.pkl"

if not os.path.exists(MODEL_FILE):

    # Load dataset
    data = pd.read_csv("price_dataset.csv")

    # Rename column
    data.columns = ["State", "Commodity", "Price"]

    # Convert to lowercase (important)
    data["State"] = data["State"].str.lower()
    data["Commodity"] = data["Commodity"].str.lower()

    # Split X and y
    X = data[["State", "Commodity"]]
    y = data["Price"]

    # Only categorical columns
    cat_cols = ["State", "Commodity"]

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])

    full_pipeline = ColumnTransformer([
        ("cat", cat_pipeline, cat_cols)
    ])

    # Transform data
    X_prepared = full_pipeline.fit_transform(X)

    # Model
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )

    model.fit(X_prepared, y)

    print("✅ Price Model trained successfully")

    # Save
    joblib.dump(full_pipeline, PIPELINE_FILE)
    joblib.dump(model, MODEL_FILE)

else:
    # Load model
    model = joblib.load(MODEL_FILE)
    pipeline = joblib.load(PIPELINE_FILE)

    # Example input (for testing)
    input_data = pd.DataFrame({
        "State": ["tamil nadu"],
        "Commodity": ["potato"]
    })

    # Transform
    X_prepared = pipeline.transform(input_data)

    # Predict
    predictions = model.predict(X_prepared)

    print("✅ Predicted Price:", predictions[0])