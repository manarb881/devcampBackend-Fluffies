# predictions/inference.py
import joblib
import pandas as pd
import os

def predict_stock(input_data):
    print("Input data for prediction:", input_data)
    try:
        # Load the trained model
        model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
        model = joblib.load(model_path)
        print("Model loaded successfully")

        # Prepare input data
        df = pd.DataFrame([input_data])
        print("Input DataFrame:", df)

        # --- ADD 'week_year' TO EXPECTED FEATURES ---
        expected_features = [
            'week_number', 'week_month', 'store_id', 'sku_id',
            'total_price', 'base_price', 'is_featured_sku', 'is_display_sku',
            'week_year' # Added week_year
        ]
        # ------------------------------------------

        # --- Feature Check (includes week_year now) ---
        missing_features = [feature for feature in expected_features if feature not in df.columns]
        if missing_features:
            # Raise specific error listing *all* missing features
            raise ValueError(f"columns are missing: {set(missing_features)}")
        # ----------------------------------------------

        # --- Preprocess data to match training (add week_year) ---
        # Ensure dtypes match expectations before model.predict
        # Note: category encoding happens INSIDE the model pipeline now usually
        # So we might only need basic type casting here.
        # Check how your model.pkl expects these (raw strings or codes?)
        # Assuming the model handles encoding:
        try:
            df['store_id'] = df['store_id'].astype(str) # Ensure string if model expects string
            df['sku_id'] = df['sku_id'].astype(int)    # Ensure int (product ID)
            df['is_featured_sku'] = df['is_featured_sku'].astype(int)
            df['is_display_sku'] = df['is_display_sku'].astype(int)
            df['week_number'] = df['week_number'].astype(int)
            df['week_month'] = df['week_month'].astype(int)
            df['week_year'] = df['week_year'].astype(int) # Added week_year processing
            df['total_price'] = df['total_price'].astype(float)
            df['base_price'] = df['base_price'].astype(float)

             # Reorder columns to exactly match the order the model expects, if necessary
             # This order depends on how your model's ColumnTransformer/Pipeline was set up.
             # If model.predict still fails, you might need to manually set the order:
             # df = df[expected_features] # Uncomment this line if needed

        except Exception as e:
             raise ValueError(f"Error during data type conversion: {e}")
        # ----------------------------------------------------------

        # Predict
        print(f"DataFrame columns before prediction: {df.columns.tolist()}")
        print(f"DataFrame dtypes before prediction:\n{df.dtypes}")
        prediction = model.predict(df[expected_features]) # Pass dataframe with correct columns
        print("Raw prediction:", prediction)

        # --- Process prediction ---
        predicted_stock = float(prediction[0])
        if predicted_stock < 0:
            predicted_stock = 0 # Ensure non-negative prediction
        print("Final predicted stock:", predicted_stock)
        return predicted_stock
        # --------------------------

    except ValueError as e: # Catch specific errors like missing features or type issues
         print(f"Prediction ValueError: {str(e)}")
         raise # Re-raise the ValueError to be caught by the view
    except FileNotFoundError as e:
         print(f"Model loading error: {str(e)}")
         raise # Re-raise FileNotFoundError
    except Exception as e:
        print(f"Unexpected prediction error: {str(e)}")
        import traceback
        traceback.print_exc() # Print detailed traceback
        raise # Re-raise any other exceptions