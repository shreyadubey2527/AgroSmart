import os
import joblib
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

from sklearn.ensemble import RandomForestClassifier

# BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# MODEL_FILE = os.path.join(BASE_DIR, "recommend_model.pkl")
# PIPELINE_FILE = os.path.join(BASE_DIR, "recommend_pipeline.pkl")
# INPUT_FILE = os.path.join(BASE_DIR, "input.csv")
# OUTPUT_FILE = os.path.join(BASE_DIR, "output.csv")


# if not os.path.exists(MODEL_FILE):
#     BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # crop/app/ml -> crop



#     DATA_FILE = os.path.join(BASE_DIR, "Crop_recommendation.csv")

#     data = pd.read_csv(DATA_FILE)
#     # print(data.describe())

#     data["temp"]=pd.cut(data["temperature"],bins=[0,10,20,30,40,50],labels=[1,2,3,4,5])

#     split=StratifiedShuffleSplit(n_splits=1,test_size=0.2,random_state=42)

#     for train_idx,test_idx in split.split(data,data["temp"]):
#         data.loc[test_idx].drop("temp",axis=1).to_csv(INPUT_FILE,index=False)
#         crop=data.loc[train_idx].drop("temp",axis=1)

#     crop_features=crop.drop("label",axis=1).copy()
#     crop_label=crop["label"]

#     pipeline=Pipeline([
#         ("imputer",SimpleImputer(strategy="median")),
#         ("scaler",StandardScaler())
#     ])
#     crop_prepared=pipeline.fit_transform(crop_features)

#     model = RandomForestClassifier(
#     n_estimators=100,
#     random_state=42
#     )    
#     model.fit(crop_prepared,crop_label)
#     print("model trained and saved")
#     joblib.dump(pipeline,PIPELINE_FILE)
#     joblib.dump(model,MODEL_FILE)
# else:
#     model=joblib.load(MODEL_FILE)
#     pipeline=joblib.load(PIPELINE_FILE)

#     input_data=pd.read_csv(INPUT_FILE)
#     features = input_data.drop("label", axis=1, errors="ignore")
#     transformed_data=pipeline.transform(features)
#     prediction=model.predict(transformed_data)
#     input_data["label"]=prediction

#     input_data.to_csv(OUTPUT_FILE,index=False)
#     print("inference complete and result saved to output.csv")
   
   

import os
import joblib
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier

# Project root folder
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # crop/app/ml -> crop

MODEL_FILE = os.path.join(BASE_DIR, "recommend_model.pkl")
PIPELINE_FILE = os.path.join(BASE_DIR, "recommend_pipeline.pkl")
OUTPUT_FILE = os.path.join(BASE_DIR, "output.csv")

DATA_FILE = os.path.join(BASE_DIR, "Crop_recommendation.csv")
data = pd.read_csv(DATA_FILE)

# Create temp bins for stratified split
data["temp"] = pd.cut(data["temperature"], bins=[0,10,20,30,40,50], labels=[1,2,3,4,5])

split = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)

for train_idx, test_idx in split.split(data, data["temp"]):
    train_data = data.loc[train_idx].drop("temp", axis=1)
    test_data = data.loc[test_idx].drop("temp", axis=1)

X_train = train_data.drop("label", axis=1)
y_train = train_data["label"]

# Preprocessing pipeline
pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

# Train model if not exists
if not os.path.exists(MODEL_FILE):
    X_train_prepared = pipeline.fit_transform(X_train)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train_prepared, y_train)
    joblib.dump(pipeline, PIPELINE_FILE)
    joblib.dump(model, MODEL_FILE)
    print("Model trained and saved.")
else:
    pipeline = joblib.load(PIPELINE_FILE)
    model = joblib.load(MODEL_FILE)

# Inference on test set
X_test = test_data.drop("label", axis=1, errors="ignore")
X_test_prepared = pipeline.transform(X_test)
predictions = model.predict(X_test_prepared)

test_data["label"] = predictions
test_data.to_csv(OUTPUT_FILE, index=False)
print(f"Inference complete. Output saved to {OUTPUT_FILE}")