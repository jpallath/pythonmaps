import tkinter as tk
from tkinter import messagebox
import googlemaps
import osmnx as ox
from geopy.distance import geodesic


# Function to geocode addresses
def geocode_address(address, api_key):
    gmaps = googlemaps.Client(key=api_key)
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        location = geocode_result[0]['geometry']['location']
        return location['lat'], location['lng']  # Return as a tuple
    else:
        raise ValueError(f"Could not geocode the address: {address}")


# Function to reverse geocode coordinates to addresses
def reverse_geocode(coord, api_key):
    gmaps = googlemaps.Client(key=api_key)
    reverse_result = gmaps.reverse_geocode(coord)
    if reverse_result:
        return reverse_result[0]['formatted_address']  # Return the human-readable address
    else:
        return "Unknown Location"


# Function to find nearby intersections within walking distance
def find_nearby_intersections(coord, radius, road_network):
    nearby_points = []
    for node, data in road_network.nodes(data=True):
        node_coord = (data['y'], data['x'])
        if geodesic(coord, node_coord).miles <= radius:
            nearby_points.append((node, node_coord))
    return nearby_points


# Function to calculate driving time between two coordinates
def calculate_driving_time(origin, destination, api_key):
    gmaps = googlemaps.Client(key=api_key)
    origin_str = f"{origin[0]},{origin[1]}"
    destination_str = f"{destination[0]},{destination[1]}"
    directions = gmaps.directions(origin_str, destination_str, mode="driving")
    if directions:
        return directions[0]['legs'][0]['duration']['value']  # Driving time in seconds
    else:
        return float('inf')  # If no route found


# Main optimization function
def optimize_locations(departure, destination, max_walk_time, api_key, road_network):
    # Geocode the departure and destination addresses
    try:
        departure_coord = geocode_address(departure, api_key)
        destination_coord = geocode_address(destination, api_key)
    except ValueError as e:
        raise ValueError(f"Geocoding error: {e}")

    # Convert walking time (minutes) to miles (~0.05 miles per minute)
    walking_radius = max_walk_time * 0.05

    # Find nearby intersections within walking radius
    departure_candidates = find_nearby_intersections(departure_coord, walking_radius, road_network)
    destination_candidates = find_nearby_intersections(destination_coord, walking_radius, road_network)

    # Calculate original driving time
    original_time = calculate_driving_time(departure_coord, destination_coord, api_key)

    # Optimize driving time
    best_time = float('inf')
    best_pickup = None
    best_dropoff = None

    for pickup_node, pickup_coord in departure_candidates:
        for dropoff_node, dropoff_coord in destination_candidates:
            time = calculate_driving_time(pickup_coord, dropoff_coord, api_key)
            if time < best_time:
                best_time = time
                best_pickup = pickup_coord
                best_dropoff = dropoff_coord

    # Reverse geocode the optimal pickup and drop-off coordinates
    best_pickup_address = reverse_geocode(best_pickup, api_key)
    best_dropoff_address = reverse_geocode(best_dropoff, api_key)

    return best_pickup_address, best_dropoff_address, best_time, original_time


# GUI application
def run_gui(api_key, road_network):
    def calculate():
        departure = entry_departure.get()
        destination = entry_destination.get()
        try:
            max_walk_time = float(entry_walk_time.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for walking time.")
            return

        try:
            optimal_pickup, optimal_dropoff, best_time, original_time = optimize_locations(
                departure, destination, max_walk_time, api_key, road_network
            )
            driving_time_diff = original_time - best_time

            result = f"Optimal Pickup Address: {optimal_pickup}\n"
            result += f"Optimal Drop-off Address: {optimal_dropoff}\n"
            result += f"Driving Time Saved: {driving_time_diff / 60:.2f} minutes"

            messagebox.showinfo("Optimization Result", result)

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    # Create GUI window
    window = tk.Tk()
    window.title("Taxi Route Optimizer")

    # Input fields
    tk.Label(window, text="Departure Address:").grid(row=0, column=0, padx=10, pady=5)
    entry_departure = tk.Entry(window, width=50)
    entry_departure.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(window, text="Destination Address:").grid(row=1, column=0, padx=10, pady=5)
    entry_destination = tk.Entry(window, width=50)
    entry_destination.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(window, text="Max Walking Time (minutes):").grid(row=2, column=0, padx=10, pady=5)
    entry_walk_time = tk.Entry(window, width=10)
    entry_walk_time.grid(row=2, column=1, padx=10, pady=5)

    # Calculate button
    btn_calculate = tk.Button(window, text="Calculate Optimal Route", command=calculate)
    btn_calculate.grid(row=3, column=0, columnspan=2, pady=20)

    window.mainloop()


# Example usage
if __name__ == "__main__":
    API_KEY = "API_KEY"


    # Load Manhattan road network
    print("Loading Manhattan road network data...")
    road_network = ox.graph_from_place("Manhattan, New York, USA", network_type="drive", simplify=True)

    # Run the GUI
    run_gui(API_KEY, road_network)
