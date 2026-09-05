# Event Contract

Required baseline fields:
- event_id
- user_id
- session_id
- event_timestamp
- event_name

Analytical dimensions may include:
- page
- product_id
- category
- device_type
- country
- traffic_source
- campaign
- experiment_id
- variant
- quantity
- price
- cart_value
- payment_method
- error_code
- event_properties

Final schema implementation belongs in `src/pulsecommerce/contracts/`.
