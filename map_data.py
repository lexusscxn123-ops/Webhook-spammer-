import json
import os

class MapData:
    def __init__(self, map_name: str = "de_dust2"):
        self.map_name = map_name
        self.data = self.load_map(map_name)
    
    def load_map(self, map_name: str) -> dict:
        config_path = os.path.join(os.path.dirname(__file__), 'map_configs', f'{map_name}.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            return {'world_size': [3000, 3000], 'center': [0, 0], 'grid_size': 500}
    
    def get_world_size(self):
        return self.data.get('world_size', [3000, 3000])
