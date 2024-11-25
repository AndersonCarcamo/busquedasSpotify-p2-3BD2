import requests 
from django.http import JsonResponse
from datetime import datetime



def get_artist(path):
    url = "https://api.spotify.com/v1/artists/" + path 
    header = {
          'Authorization' : 'Bearer BQAOAOz307XVnW1ypci9z0l_UlgG3En4f-spT0b11ispCIFq7TJj1JnCX-FMTnj4ACR9u8t1GsVp35NIhsKs1OBSUlBO6pAcAT0OBrb9XkLzuhAPV6g'
    }

    response = requests.get(url, headers=header )
    try:
        return response.json()
    except requests.exceptions.HTTPError as e:
        return JsonResponse({"error": str(e)})

#for i in get_artist("0OdUWJ0sBjDrqHygGUXeCF"):
#    print(i)

def get_track(track_id):
    url = f"https://api.spotify.com/v1/tracks/{track_id}"  # Usamos el ID de la pista
    header = {
        'Authorization': 'Bearer BQAOAOz307XVnW1ypci9z0l_UlgG3En4f-spT0b11ispCIFq7TJj1JnCX-FMTnj4ACR9u8t1GsVp35NIhsKs1OBSUlBO6pAcAT0OBrb9XkLzuhAPV6g'
    }

    response = requests.get(url, headers=header)
    try:
        return response.json()
    except requests.exceptions.HTTPError as e:
        return JsonResponse({"error": str(e)})

track_data = get_track("11dFghVXANMlKmJXsNCbNl")
for key, value in track_data.items():
    if key == "preview_url":
        print(value)






    
def get_game_info_api(id):
    fields = "fields followers, genres ;"
    body = fields + " where id = " + str(id) + ";"
    data = get_projects("0OdUWJ0sBjDrqHygGUXeCF").json()
    try:
        return {
            'api_id': id,
            'followers': data["followers"],
            'genres': data["genres"],
        }
    except:
        return JsonResponse({"error": "Not found"})

#print (get_game_info_api("0OdUWJ0sBjDrqHygGUXeCF"))