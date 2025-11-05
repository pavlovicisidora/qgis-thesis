# -*- coding: utf-8 -*-
"""
Module for querying OpenStreetMap Overpass API.
"""
import time
import requests
import json

class OverpassAPI:
    """
    Handler for Overpass API queries to download POI data from OpenStreetMap.
    """
    
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    TIMEOUT = 60
    
    RISK_ZONES = {
        'factory': ('man_made', 'works'),
        'gas station': ('amenity', 'fuel'),
        'power plant': ('power', 'plant'),
        'power substation': ('power', 'substation'),
        'railway station': ('railway', 'station'),
        'railway halt': ('railway', 'halt'),
        'waterworks': ('man_made', 'water_works'),
        'wastewater plant': ('man_made', 'wastewater_plant'),
        'industrial zone': ('landuse', 'industrial'),
    }

    VULNERABLE_POPULATIONS = {
        'school': ('amenity', 'school'),
        'kindergarten': ('amenity', 'kindergarten'),
        'hospital': ('amenity', 'hospital'),
        'clinic': ('amenity', 'clinic'),
        'nursing home': ('amenity', 'nursing_home'),
        'social facility': ('amenity', 'social_facility'),
        'childcare': ('amenity', 'childcare'),
        'community centre': ('amenity', 'community_centre'),
    }
    
    CATEGORY_MAPPING = {**RISK_ZONES, **VULNERABLE_POPULATIONS}
    
    @staticmethod
    def build_query(bbox, poi_type):
        """
        Build an Overpass QL query for POIs within a bounding box.
        
        Args:
            bbox: Tuple of (south, west, north, east) in WGS84 coordinates
            poi_type: String, the POI category  
        
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
    def build_batch_query(bbox, poi_types):
        """
        Build an Overpass QL query for multiple POI types in one request.
        
        Args:
            bbox: Tuple of (south, west, north, east) in WGS84 coordinates
            poi_types: List of POI category strings
        
        Returns:
            String containing the Overpass QL query
        """
        south, west, north, east = bbox
        
        queries = []
        for poi_type in poi_types:
            tag_key, tag_value = OverpassAPI.CATEGORY_MAPPING.get(
                poi_type.lower(),
                ('amenity', poi_type.lower())
            )
            queries.append(f'  node["{tag_key}"="{tag_value}"]({south},{west},{north},{east});')
            queries.append(f'  way["{tag_key}"="{tag_value}"]({south},{west},{north},{east});')
        
        query = f"""
            [out:json][timeout:60];
            (
            {chr(10).join(queries)}
            );
            out center;
            """
        
        return query
    
    @staticmethod
    def query_overpass(bbox, poi_type, retry_count=3):
        """
        Query the Overpass API with retry logic.
        
        Args:
            bbox: Tuple of (south, west, north, east) in WGS84 coordinates
            poi_type: String, the POI category
            retry_count: Number of retry attempts
        
        Returns:
            Dictionary containing the API response
        """
        query = OverpassAPI.build_query(bbox, poi_type)
        
        for attempt in range(retry_count):
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
                if attempt < retry_count - 1:
                    wait_time = (attempt + 1) * 2 
                    print(f"Timeout on attempt {attempt + 1}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception("Request timed out after multiple attempts. Try a smaller area.")
            
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 504:
                    if attempt < retry_count - 1:
                        wait_time = (attempt + 1) * 3
                        print(f"Server timeout on attempt {attempt + 1}, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise Exception("Server timeout after multiple attempts. The area may be too large or the server is overloaded.")
                elif e.response.status_code == 429: 
                    if attempt < retry_count - 1:
                        wait_time = (attempt + 1) * 5
                        print(f"Rate limited on attempt {attempt + 1}, waiting {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise Exception("Rate limited by API. Please wait a moment and try again.")
                else:
                    raise Exception(f"HTTP error from Overpass API: {e}")
            
            except requests.exceptions.ConnectionError:
                raise Exception("Could not connect to Overpass API. Check your internet connection.")
            
            except json.JSONDecodeError:
                raise Exception("Invalid response from Overpass API.")
            
            except Exception as e:
                raise Exception(f"Error querying Overpass API: {str(e)}")
    
    @staticmethod
    def query_overpass_batch(bbox, poi_types):
        """
        Query the Overpass API for multiple POI types at once.
        
        Args:
            bbox: Tuple of (south, west, north, east) in WGS84 coordinates
            poi_types: List of POI category strings
        
        Returns:
            Dictionary containing the API response
        """
        query = OverpassAPI.build_batch_query(bbox, poi_types)
        
        try:
            response = requests.post(
                OverpassAPI.OVERPASS_URL,
                data={'data': query},
                timeout=90  
            )
            
            response.raise_for_status()
            data = response.json()
            return data
            
        except requests.exceptions.Timeout:
            raise Exception("Batch request timed out. Try selecting fewer categories or a smaller area.")
        
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to Overpass API. Check your internet connection.")
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 504:
                raise Exception("Server timeout. Try selecting fewer categories or a smaller area.")
            else:
                raise Exception(f"HTTP error from Overpass API: {e}")
        
        except json.JSONDecodeError:
            raise Exception("Invalid response from Overpass API.")
        
        except Exception as e:
            raise Exception(f"Error querying Overpass API: {str(e)}")
        
    @staticmethod
    def parse_features(api_response):
        """
        Parse Overpass API response and extract POI features.
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
                       tags.get('man_made') or
                       tags.get('power') or
                       tags.get('landuse') or
                       tags.get('healthcare') or
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
    
    @staticmethod
    def parse_batch_features(api_response):
        """
        Parse batch query response and group features by category.
        
        Returns:
            Dictionary with category names as keys and feature lists as values
        """
        all_features = OverpassAPI.parse_features(api_response)
        
        categorized = {}
        
        for feature in all_features:
            tags = feature.get('tags', {})
            
            category = None
            for cat_name, (tag_key, tag_value) in OverpassAPI.CATEGORY_MAPPING.items():
                if tags.get(tag_key) == tag_value:
                    category = cat_name
                    break
            
            if category:
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(feature)
        
        return categorized
    
    