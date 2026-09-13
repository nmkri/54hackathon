## Blueoop

Blueoop is a pricing algorithm that determines the optimal pricing for a truck based only on it's image. It uses a custom VLM to extract the truck's model and condition from its image. 

## Dataset

## VLM Training

- **Phase 0:** Take a stratified sample of 200 images and label the `primary_subject` for each of those images. Lock it into a JSON schema, which is used to determine the rest of the images