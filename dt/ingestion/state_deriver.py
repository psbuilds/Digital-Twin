import math
from dt.models.twin_state import TwinState
from dt.utils.exceptions import StateDerivationError


def derive_twin_state(raw: dict) -> TwinState:
    """
    Function that is used to convert raw data from the dataset to a format where it is acceptable by the DT.
        - u10,v10 are not stored directly -> converted to wind speed and direction  
    """
    try:
        u10, v10 = raw["u10"], raw["v10"]               #u10 - horizontal wind component v10 - vertical wind component 

        # u and v are perpendicular components of wind thus we take root(u^2+v^2) to find out the wind speed  
        wind_speed = math.sqrt(u10**2 + v10**2)                   

        # atan2 ->convert to radians then make it pos by adding 360 then convert to degrees to return the relative direction of wind
        wind_direction = (math.degrees(math.atan2(u10, v10)) + 360) % 360

        #temprateure at 2 meter is converted to C from Kelvin 
        temperature = raw["t2m"] - 273.15               

        # precipitatin is converted to milli-meters
        precipitation = raw.get("tp", 0.0) * 1000

        return TwinState(
            grid_id=raw["grid_id"],
            timestamp=raw["time"],
            latitude=raw["lat"],
            longitude=raw["lon"],
            wind_speed=round(wind_speed, 2),
            wind_direction=round(wind_direction, 1),
            temperature=round(temperature, 2),
            precipitation=round(precipitation, 2),
            pm25=raw["pm2p5"],
            pm10=raw["pm10"],
            no2=raw["no2"],
            o3=raw["o3"],
            so2=raw["so2"],
            co=raw["co"],
            sea_surface_temp=raw.get("sst"),
            is_coastal=raw.get("sst") is not None,
        )
    except Exception as e:
        raise StateDerivationError(str(e))
