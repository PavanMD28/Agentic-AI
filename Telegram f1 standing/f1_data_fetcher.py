import requests

def get_f1_standings():
    url = "http://ergast.com/api/f1/current/driverStandings.json"
    try:
        print(f"Fetching F1 standings from: {url}")
        response = requests.get(url)
        print(f"Response status code: {response.status_code}")
        data = response.json()
        
        print("Successfully parsed JSON response")
        standings = []
        standings_list = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
        print(f"Found {len(standings_list)} drivers in standings")
        
        for standing in standings_list:
            position = standing['position']
            driver_name = f"{standing['Driver']['givenName']} {standing['Driver']['familyName']}"
            points = standing['points']
            
            standings.append({
                'position': position,
                'driver': driver_name,
                'points': points
            })
            print(f"Added driver: {driver_name} in position {position} with {points} points")
            
        if not standings:
            print("Warning: No standings data found")
            return None
            
        print(f"Successfully retrieved {len(standings)} standings")
        return standings
        
    except Exception as e:
        print(f"Error fetching F1 standings: {e}")
        print(f"Error type: {type(e).__name__}")
        return None