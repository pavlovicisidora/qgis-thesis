# -*- coding: utf-8 -*-
"""
Module for querying OpenStreetMap Overpass API.
"""
import requests
import json

class OverpassAPI:
    """
    Handler for Overpass API queries to download POI data from OpenStreetMap.
    """
    
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    TIMEOUT = 100000
    
    CATEGORY_MAPPING = {
        'restaurant': ('amenity', 'restaurant'),
        'cafe': ('amenity', 'cafe'),
        'hospital': ('amenity', 'hospital'),
        'school': ('amenity', 'school'),
        'bank': ('amenity', 'bank'),
        'atm': ('amenity', 'atm'),
        'pharmacy': ('amenity', 'pharmacy'),
        'gas station': ('amenity', 'fuel'),
        'supermarket': ('shop', 'supermarket'),
        'mall': ('shop', 'mall'),
        'bus station': ('amenity', 'bus_station'),
        'train station': ('railway', 'station'),
        'hotel': ('tourism', 'hotel'),
    }
    
    @staticmethod
    def build_query(bbox, poi_type):
        """
        Build an Overpass QL query for POIs within a bounding box.
        
        Args:
            bbox: Tuple of (south, west, north, east) in WGS84 coordinates
            poi_type: String, the POI category (e.g., 'restaurant', 'hospital')
        
        Returns:
            String containing the Overpass QL query
        """
        south, west, north, east = bbox
        
        tag_key, tag_value = OverpassAPI.CATEGORY_MAPPING.get(
            poi_type.lower(),
            ('amenity', poi_type.lower())
        )
        
        query = f"""
        [out:json][timeout:25];
        (
        node["{tag_key}"="{tag_value}"]({south},{west},{north},{east});
        way["{tag_key}"="{tag_value}"]({south},{west},{north},{east});
        );
        out center;
        """
        
        return query
    
    @staticmethod
    def query_overpass(bbox, poi_type):
        """
        Query the Overpass API and return POI data.
        
        Args:
            bbox: Tuple of (south, west, north, east) in WGS84 coordinates
            poi_type: String, the POI category
        
        Returns:
            Dictionary containing the API response, or None on error
        
        Raises:
            requests.exceptions.RequestException: On network/API errors
        """
        query = OverpassAPI.build_query(bbox, poi_type)
        
        try:
            response = requests.post(
                OverpassAPI.OVERPASS_URL,
                data={'data': query},
                timeout=OverpassAPI.TIMEOUT
            )
            
            response.raise_for_status()
            
            data = response.json()
            
            return data
            
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Try a smaller area or check your internet connection.")
        
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to Overpass API. Check your internet connection.")
        
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error from Overpass API: {e}")
        
        except json.JSONDecodeError:
            raise Exception("Invalid response from Overpass API.")
        
        except Exception as e:
            raise Exception(f"Error querying Overpass API: {str(e)}")
    
    @staticmethod
    def parse_features(api_response):
        """
        Parse Overpass API response and extract POI features.
        
        Args:
            api_response: Dictionary from Overpass API
        
        Returns:
            List of dictionaries, each containing:
                - 'lat': Latitude
                - 'lon': Longitude
                - 'name': POI name (or 'Unnamed' if not available)
                - 'type': POI type/category
                - 'id': OSM ID
                - 'tags': Dictionary of all OSM tags
        """
        features = []
        
        if 'elements' not in api_response:
            return features
        
        for element in api_response['elements']:
            element_type = element.get('type')
            
            lat = None
            lon = None
            
            if element_type == 'node':
                lat = element.get('lat')
                lon = element.get('lon')
            elif element_type == 'way':
                center = element.get('center', {})
                lat = center.get('lat')
                lon = center.get('lon')
            else:
                continue
            
            if lat is None or lon is None:
                continue
            
            tags = element.get('tags', {})
            
            name = tags.get('name', 'Unnamed')
            
            poi_type = (tags.get('amenity') or 
                       tags.get('shop') or 
                       tags.get('tourism') or 
                       tags.get('railway') or 
                       'unknown')
            
            osm_id = element.get('id', 0)
            
            feature = {
                'lat': lat,
                'lon': lon,
                'name': name,
                'type': poi_type,
                'id': osm_id,
                'tags': tags
            }
            
            features.append(feature)
        
        return features
    