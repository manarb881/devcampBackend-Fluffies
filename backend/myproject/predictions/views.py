# backend/predictions/views.py

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import StockPrediction
from .serializers import StockPredictionSerializer
from .inference import predict_stock
from products.models import Product
import traceback
import datetime # Make sure datetime is imported

# View for Creating a new Stock Prediction
class StockPredictionCreateView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = StockPrediction.objects.all() # Needed for generic view, but we override create
    serializer_class = StockPredictionSerializer

    def create(self, request, *args, **kwargs):
        print(f"Received POST request data: {request.data}")
        # Initialize serializer with request data
        # Note: We don't pass instance=... because we are creating
        serializer = self.get_serializer(data=request.data)

        # Validate the incoming data (checks 'product_id', 'date', prices, etc.)
        if not serializer.is_valid():
            print(f"Serializer validation errors: {serializer.errors}")
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # If valid, validated_data contains processed input
        # including the 'product' instance and 'date' object
        validated_data = serializer.validated_data
        product_instance = validated_data['product'] # Fetch related Product object
        input_date = validated_data['date']         # Fetch date object

        print(f"Serializer validated data: {validated_data}")

        # --- Derive features needed by the model ---
        the_month = input_date.month
        the_year = input_date.year
        # --- Week Calculation Logic (verify this matches model training) ---
        day_of_month = input_date.day
        first_day_of_month = input_date.replace(day=1)
        first_day_weekday = first_day_of_month.weekday() # Monday=0, Sunday=6
        # Calculate week number (assuming week starts Monday, adjust if needed)
        week_number = (day_of_month + first_day_weekday - 1) // 7 + 1
        # --- End Week Calculation ---

        # Ensure week is within 1-5 range (basic capping)
        week_number = max(1, min(week_number, 5))

        print(f"Derived features - Week: {week_number}, Month: {the_month}, Year: {the_year}")

        # --- Prepare input dictionary EXACTLY as predict_stock expects ---
        input_data_for_model = {
            'week_number': week_number,
            'week_month': the_month,           # Use 'week_month' if model expects that name
            'store_id': validated_data['store_id'],
            'sku_id': product_instance.id,      # Use Product ID
            'total_price': validated_data['total_price'],
            'base_price': validated_data['base_price'],
            'is_featured_sku': validated_data['is_featured_sku'],
            'is_display_sku': validated_data['is_display_sku'],
            'week_year': the_year,             # Use 'week_year' if model expects that name
        }

        # --- Call the prediction function ---
        final_predicted_stock = None # Initialize
        try:
            print(f"Data being sent to prediction function: {input_data_for_model}")
            # This function should return a single numeric value (float or int)
            predicted_stock_raw = predict_stock(input_data_for_model)
            print(f"Raw prediction result from inference: {predicted_stock_raw} (type: {type(predicted_stock_raw)})")

            # Validate and clean the prediction result
            if predicted_stock_raw is None or not isinstance(predicted_stock_raw, (int, float)):
                 # Log the unexpected type for debugging
                 print(f"Error: Prediction function returned an invalid type: {type(predicted_stock_raw)}")
                 raise ValueError("Prediction function returned an invalid value.")

            # Ensure it's a float for consistency, handle potential negative values
            final_predicted_stock = float(predicted_stock_raw)
            if final_predicted_stock < 0:
                print(f"Warning: Raw prediction was negative ({final_predicted_stock}), setting to 0.")
                final_predicted_stock = 0.0

            print(f"Final processed predicted stock: {final_predicted_stock}")

        # --- Exception Handling for Prediction ---
        except ValueError as e: # Specific errors from prediction logic (e.g., missing columns, type issues)
            error_message = f"Prediction data error: {str(e)}"
            print(error_message)
            return Response({"errors": {"prediction": error_message}}, status=status.HTTP_400_BAD_REQUEST)
        except FileNotFoundError as e: # Model file missing
            error_message = f"Model file not found: {str(e)}"
            print(error_message)
            return Response({"errors": {"prediction": error_message}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ModuleNotFoundError as e: # Missing dependency for model loading
             error_message = f"Missing library for model: {str(e)}. Please install it."
             print(error_message)
             return Response({"errors": {"prediction": error_message}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e: # Catch-all for unexpected errors during prediction
            error_message = f"Prediction failed unexpectedly: {str(e)}"
            print(error_message)
            traceback.print_exc() # Log the full traceback for server debugging
            return Response({"errors": {"prediction": error_message}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- Save the prediction to the database ---
        # We use serializer.save(), passing any fields NOT derived directly from request data.
        # The serializer instance already knows about 'store_id', 'total_price' etc from validated_data.
        # It also knows the 'product' instance.
        try:
            instance = serializer.save(
                predicted_stock=final_predicted_stock, # Pass the calculated prediction
                week_number=week_number,               # Pass the derived week number
                month=the_month                         # Pass the derived month
            )
            print(f"Successfully saved StockPrediction instance with ID: {instance.id}")
        except Exception as e:
             # Handle potential database saving errors
             error_message = f"Database save failed: {str(e)}"
             print(error_message)
             traceback.print_exc()
             return Response({"errors": {"database": error_message}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- Prepare and return the final successful response ---
        # We re-serialize the created 'instance' to include all read-only fields
        # (like 'id', 'product' details, 'predicted_stock', 'created_at') in the response.
        response_serializer = self.get_serializer(instance)
        headers = self.get_success_headers(response_serializer.data)
        print(f"Returning successful response data: {response_serializer.data}")
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# View for Listing existing Stock Predictions
class StockPredictionListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    # Add ordering to prevent pagination warnings and ensure consistent results
    queryset = StockPrediction.objects.all().order_by('-created_at')
    serializer_class = StockPredictionSerializer
    # Consider adding pagination_class = YourPaginationClass if using pagination