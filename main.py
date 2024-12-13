import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from datetime import datetime, timedelta
import json 

class City:
    """
    Represents a city with a name and coordinates.
    """
    def __init__(self, name, coordinates):
        """
        Initializes a City object.

        Args:
            name (str): The name of the city.
            coordinates (tuple): The coordinates of the city (longitude, latitude).
        """
        self.name = name
        self.coordinates = coordinates

    def normalize_coordinates(self, min_x=8, max_x=13, min_y=54, max_y=58):
        """
        Normalizes the coordinates of the city to a range between -1 and 1.

        Args:
            min_x (float): Minimum x-coordinate for normalization.
            max_x (float): Maximum x-coordinate for normalization.
            min_y (float): Minimum y-coordinate for normalization.
            max_y (float): Maximum y-coordinate for normalization.

        Returns:
            tuple: Normalized coordinates (x, y).
        """
        norm_x = (self.coordinates[0] - min_x) / (max_x - min_x) * 2 - 1
        norm_y = (self.coordinates[1] - min_y) / (max_y - min_y) * 2 - 1
        return (norm_x, norm_y)

class Connection:
    """
    Represents a connection between two cities with a duration.
    """
    def __init__(self, start_city, end_city, duration):
        """
        Initializes a Connection object.

        Args:
            start_city (str): The name of the starting city.
            end_city (str): The name of the ending city.
            duration (float): The duration of the connection in hours.
        """
        self.start_city = start_city
        self.end_city = end_city
        self.duration = duration

class RailNetwork:
    """
    Represents a rail network consisting of cities and connections.
    """
    def __init__(self):
        """
        Initializes a RailNetwork object.
        """
        self.cities = {}
        self.connections = []
        self.graph = nx.Graph()

    def add_city(self, city):
        """
        Adds a city to the rail network.

        Args:
            city (City): The city to add.
        """
        self.cities[city.name] = city

    def add_connection(self, connection):
        """
        Adds a connection to the rail network.

        Args:
            connection (Connection): The connection to add.
        """
        self.connections.append(connection)

    def build_graph(self):
        """
        Builds a graph representation of the rail network.
        """
        for city in self.cities.values():
            self.graph.add_node(city.name)
        for connection in self.connections:
            self.graph.add_edge(connection.start_city, connection.end_city, weight=connection.duration)

    def load_from_json(self, json_file):
        """
        Loads cities and connections from a JSON file.

        Args:
            json_file (str): The path to the JSON file.
        """
        with open(json_file, 'r') as file:
            data = json.load(file)
            for city_data in data['cities']:
                city = City(city_data['name'], tuple(city_data['coordinates']))
                self.add_city(city)
            for connection_data in data['connections']:
                connection = Connection(connection_data['start_city'], connection_data['end_city'], connection_data['duration'])
                self.add_connection(connection)

class RailNetworkVisualizer:
    """
    Visualizes a rail network using matplotlib and networkx.
    """
    def __init__(self, rail_network, show_live=True, duration=60):
        """
        Initializes a RailNetworkVisualizer object.

        Args:
            rail_network (RailNetwork): The rail network to visualize.
            show_live (bool): Whether to show the animation live.
            duration (int): The total duration of the video in seconds.
        """
        self.rail_network = rail_network
        self.show_live = show_live
        self.duration = duration
        self.fig, self.ax = plt.subplots(figsize=(7.75, 10.24))
        self.img = None
        self.pos = {city.name: city.normalize_coordinates() for city in rail_network.cities.values()}
        self.start_time = datetime.strptime("06:00", "%H:%M")
        self.current_time = self.start_time
        self.total_frames = 0
        self.stop_durations = []
        self.calculate_frames_and_stops()

    def calculate_frames_and_stops(self):
        """
        Calculates the total number of frames and stop durations for the animation.
        """
        total_travel_time = sum([connection.duration for connection in self.rail_network.connections])
        total_stop_time = total_travel_time * 0.2  # stop time as 20% of total travel time
        self.stop_durations = [total_stop_time / len(self.rail_network.connections)] * len(self.rail_network.connections)
        self.total_frames = self.duration * 10  # Total frames based on the duration in seconds

    def load_background(self, image_path):
        """
        Loads a background image for the animation.

        Args:
            image_path (str): The path to the background image.
        """
        self.img = plt.imread(image_path)
        self.ax.imshow(self.img, extent=[-1, 1, -1, 1]) # square display

    def draw_network(self):
        """
        Draws the rail network on the plot.
        """
        nx.draw(self.rail_network.graph, self.pos, with_labels=True, node_size=700, node_color='skyblue', alpha=0.7, font_size=10, font_weight='bold', ax=self.ax)

    def update(self, frame):
        """
        Updates the animation for each frame.

        Args:
            frame (int): The current frame number.
        """
        self.ax.clear()
        self.ax.imshow(self.img , extent=[-1, 1, -1, 1]) # square display
        self.draw_network()

        cumulative_frames = 0
        for idx, connection in enumerate(self.rail_network.connections):
            travel_frames = self.total_frames // len(self.rail_network.connections)
            stop_frames = int(self.stop_durations[idx] * 10)
            # Check if the current frame is within the travel or stop frames for the connection
            if cumulative_frames <= frame < cumulative_frames + travel_frames:
                i = frame - cumulative_frames
                x_start, y_start = self.pos[connection.start_city]
                x_end, y_end = self.pos[connection.end_city]
                x = x_start + (x_end - x_start) * i / travel_frames
                y = y_start + (y_end - y_start) * i / travel_frames
                self.ax.plot(x, y, 'rs')  # Train as a red square
                self.current_time += timedelta(hours=connection.duration * (1 / travel_frames))
                break
            # 
            elif cumulative_frames + travel_frames <= frame < cumulative_frames + travel_frames + stop_frames:
                x, y = self.pos[connection.end_city]
                self.ax.plot(x, y, 'rs')  # Train as a red square
                self.current_time += timedelta(minutes=self.stop_durations[idx] / 10)  # Adjust the timer for the stop duration
                break
            cumulative_frames += travel_frames + stop_frames

        self.ax.text(-0.95, 0.95, self.current_time.strftime("%H:%M"), fontsize=12, bbox=dict(facecolor='white', alpha=0.8))

    def animate(self, output_format='mp4'):
        """
        Animates the rail network and saves the animation to a file.

        Args:
            output_format (str): The format to save the animation ('mp4' or 'gif').

        If show_live is True, the animation is displayed live.
        """
        self.rail_network.build_graph()
        self.load_background("src/map-of-denmark.jpg")
        self.draw_network()
        ani = FuncAnimation(self.fig, self.update, frames=self.total_frames, repeat=True)
        
        # Save the animation to a file (.mp4 or .gif formats)
        if output_format == 'mp4':
            ani.save("rail_network_animation.mp4", writer='ffmpeg', fps=24)  
        elif output_format == 'gif':
            ani.save("rail_network_animation.gif", writer=PillowWriter(fps=24))

        if self.show_live:  # Check if live display is enabled
            plt.show()  # Display the animation

# Example usage:
rail_network = RailNetwork()
rail_network.load_from_json('src/rail_network_data.json')  # Load data from JSON file

visualizer = RailNetworkVisualizer(rail_network, show_live=False, duration=12)  # disable matplotlib 'live' graphing and set duration to 12 seconds
visualizer.animate(output_format='gif')  # Save as GIF instead of mp4