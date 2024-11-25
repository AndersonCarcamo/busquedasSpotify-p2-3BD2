import requests


# Set up the endpoint URL and parameters
url = "https://api.spotify.com/v1/albums/{id}/tracks"
headers = {
    "Authorization": "Bearer BQDPvhAbfIcpsme0IY8lCzvLK4MiPXEFwOl5gwIVcKi0IvFUkNORd0zBaFRBwvnKG1G4xBOxyw-Qh14UTp48cTHKycQf2_MBmqZzR5nn8eldkj6r3Y0",
    "Content-Type": "application/json"
}
params = {
    "market": "US"
}


# Make the request to the API
response = requests.get(url.format(id="4aawyAB9vmqN3uQ7FjRGTy"), headers=headers, params=params)

# Check if the request was successful
if response.status_code == 200:
    # Get the JSON data from the response
    data = response.json()

    # Loop through the tracks in the album
    for track in data['items']:
        # Check if the track has a preview URL
        if 'preview_url' in track:
            # Print the preview URL for the track
            print(f"Preview URL for {track['name']}: {track['preview_url']}")

else:
    print(f"Request failed with status code {response.status_code}")


