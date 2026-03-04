def calculate_sub_index(pollutant, concentration):
    """
    Calculates the sub-index for a given pollutant and concentration according to Indian AQI standards.
    """
    if concentration is None or concentration < 0:
        return None

    # Breakpoints for pollutants (Conc_Lo, Conc_Hi, Index_Lo, Index_Hi)
    breakpoints = {
        'pm10': [
            (0, 50, 0, 50), (51, 100, 51, 100), (101, 250, 101, 200),
            (251, 350, 201, 300), (351, 430, 301, 400), (430, 9999, 401, 500)
        ],
        'pm25': [
            (0, 30, 0, 50), (31, 60, 51, 100), (61, 90, 101, 200),
            (91, 120, 201, 300), (121, 250, 301, 400), (250, 9999, 401, 500)
        ],
        'no2': [
            (0, 40, 0, 50), (41, 80, 51, 100), (81, 180, 101, 200),
            (181, 280, 201, 300), (281, 400, 301, 400), (400, 9999, 401, 500)
        ],
        'so2': [
            (0, 40, 0, 50), (41, 80, 51, 100), (81, 380, 101, 200),
            (381, 800, 201, 300), (801, 1600, 301, 400), (1600, 9999, 401, 500)
        ],
        'co': [
            (0, 1.0, 0, 50), (1.1, 2.0, 51, 100), (2.1, 10, 101, 200),
            (10.1, 17, 201, 300), (17.1, 34, 301, 400), (34, 9999, 401, 500)
        ],
        'o3': [
            (0, 50, 0, 50), (51, 100, 51, 100), (101, 168, 101, 200),
            (169, 208, 201, 300), (209, 748, 301, 400), (748, 9999, 401, 500)
        ],
        # Adding NH3 for completeness if needed
        'nh3': [
            (0, 200, 0, 50), (201, 400, 51, 100), (401, 800, 101, 200),
            (801, 1200, 201, 300), (1201, 1800, 301, 400), (1800, 9999, 401, 500)
        ]
    }

    if pollutant not in breakpoints:
        return None

    for (b_lo, b_hi, i_lo, i_hi) in breakpoints[pollutant]:
        if b_lo <= concentration <= b_hi:
            return round(((i_hi - i_lo) / (b_hi - b_lo)) * (concentration - b_lo) + i_lo)
    
    # If concentration exceeds highest breakpoint
    max_bp = breakpoints[pollutant][-1]
    if concentration > max_bp[1]:
        return max_bp[3]

    return None

def calculate_overall_aqi(pollutants):
    """
    Calculates the overall Indian AQI based on a dictionary of pollutant concentrations.
    Expected keys: 'pm25', 'pm10', 'no2', 'so2', 'co', 'o3', 'nh3'
    Returns: int (AQI) or None
    """
    sub_indices = []
    
    # Requirement: At least 3 pollutants must be present, one of them must be either PM2.5 or PM10
    has_particulate = False
    
    for pollutant, concentration in pollutants.items():
        sub_index = calculate_sub_index(pollutant, concentration)
        if sub_index is not None:
            sub_indices.append(sub_index)
            if pollutant in ['pm25', 'pm10']:
                has_particulate = True
    
    if len(sub_indices) >= 3 and has_particulate:
        return max(sub_indices)
    elif len(sub_indices) > 0:
        # Fallback if less than 3 but has some data
        return max(sub_indices)
    
    return None
