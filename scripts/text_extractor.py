import re
import pandas as pd
from typing import Optional, List, Literal
from tqdm import tqdm

class PropertyInfoExtractor:
    '''Helper class to recover missing values from description/title for this dataset'''

    interior_patterns = {
        'cao cấp': re.compile(r'nội\s*thất\s*cao\s*cấp'),
        'đầy đủ': re.compile(r'(đầy\s*đủ\s*nội\s*thất|full\s*nội\s*thất|nội\s*thất\s*đầy\s*đủ|full\s*đồ)'),
        'cơ bản': re.compile(r'(nội\s*thất\s*cơ\s*bản|đồ\s*cơ\s*bản)'),
        'chưa có': re.compile(r'(chưa\s*có\s*nội\s*thất|nội\s*thất\s*trống|không\s*(?:có)?\s*nội\s*thất|nhà\s*trống)')
    }
    n_floors_patterns = {
        'exclude':[
            re.compile(r'(?:gpxd|giấy phép xây dựng)\s*\d+\s*(?:tầng|lầu)'), 
            re.compile(r'hồ bơi 3 tầng')
        ],
        'simple_floor_count': re.compile(r'(\d+(?:[.,]\d*)?)\s*tầng'),
        'count_by_structure': re.compile(r"(?:\d+)?\s*trệt\s*[+,]?\s*(?:\d+)?\s*(?:lửng|gác|tầng\s*áp\s*mái)?\s*[+,]?\s*(\d+)\s*(?:lầu)"),
    }
    has_mezzanine_pattern = re.compile(r"(?:có)?\s*(?:lửng|gác|tầng\s*áp\s*mái)")
    front_road_width_pattern = re.compile(r"(?:đường|hẻm|ngõ|trục đường)\s*(?:trước\s*nhà|trước)?\s*(?:rộng|nội\s*bộ)?\s*(\d+(?:[.,]\d*)?)\s*(?:m|met|mét)")
    front_width_patterns = {
        'dimensions': re.compile(r"(\d+(?:[.,]\d*)?)\s*(?:m|met|mét)?\s*[x]\s*\d+(?:[.,]\d*)?\s*(?:m|met|mét)?"),
        'keywords': re.compile(r'(?:mặt\s*tiền|ngang)[^\d]{0,10}(\d+(?:[.,]\d*)?)\s?(?:m|met|mét)'),
        'edge_case': re.compile(r'(\d+(?:[.,]\d*)?)\s*(?:m|met|mét)\s*(?:giáp\s*đường)')
    }
    facing_direction_patterns = {
        'find_direction': re.compile(r'(?:cửa|cổng|nhà|cửa\s*chính|cổng\s*chính)?\s*(?:hướng|quay|quay\s*hướng|xoay|xoay\s*hướng)\s*(?:cửa|cổng|nhà|cửa\s*chính|cổng\s*chính)?\s*(đông\s*bắc|đông\s*nam|tây\s*bắc|tây\s*nam|đông|tây|nam|bắc)'),
        'house_direction_validator': re.compile(r'(?:cửa|cổng|nhà|cửa\s*chính|cổng\s*chính)')
    }
    balcony_direction_pattern = re.compile(r'(?:hướng|quay|quay\s*hướng|xoay|xoay\s*hướng)?\s*ban\s*công\s*(?:hướng|quay|quay\s*hướng|xoay|xoay\s*hướng)?\s*(đông\s*bắc|đông\s*nam|tây\s*bắc|tây\s*nam|đông|tây|nam|bắc)')
    EXTRACT_FUNCS = ["front_road_width", "front_width", "n_floors", "interior", "facing_direction", "balcony_direction", "has_mezzanine"]

    def __init__(self, text, context_r:int=-1, verbose:bool=True):
        if not text or not isinstance(text, str) or not text.strip():
            self.text = None
        else:
            self.text = text.lower().strip()
        self.context_r = context_r
        self.verbose = verbose


    def interior(self):
        if (matched := self.interior_patterns['cao cấp'].search(self.text)):
            context = self.pattern_match_surroundings(matched.group(0))
            return "cao cấp", context
        if (matched := self.interior_patterns['đầy đủ'].search(self.text)):
            context = self.pattern_match_surroundings(matched.group(0))
            return "đầy đủ", context
        if (matched := self.interior_patterns['cơ bản'].search(self.text)):
            context = self.pattern_match_surroundings(matched.group(0))
            return "cơ bản", context
        if (matched := self.interior_patterns['chưa có'].search(self.text)):
            context = self.pattern_match_surroundings(matched.group(0))
            return "chưa có", context
        return None, ''


    def n_floors(self) -> Optional[int]:
        if not self.text:
            return None, ''
        normalized_text = self.text.replace('-', '').replace('+', '').replace(':','')

        # Exclusion cases: giấy phép xd cho bds, số tầng nhiễu (hồ bơi 3 tầng)
        for pattern in self.n_floors_patterns['exclude']:
            if (matched := pattern.search(normalized_text)):
                context = self.pattern_match_surroundings(matched.group(0), alternate_str=normalized_text)
                return None, context

        # Inclusion case 1: Simple Floor Count (\d+ tầng)
        matches = list(self.n_floors_patterns['simple_floor_count'].finditer(normalized_text))
        if matches:
            values_contexts = [(
                int(float(m.group(1).replace(',', '.'))),
                self.pattern_match_surroundings(m.group(0), alternate_str=normalized_text)
            ) for m in matches]
            
            return max(values_contexts) if values_contexts else (None, '')

        
        # Inclusion case 2: Format "Trệt + Lầu/Tầng" (use compiled)
        match_tret_lau = self.n_floors_patterns['count_by_structure'].search(normalized_text)
        if match_tret_lau:
            context = self.pattern_match_surroundings(match_tret_lau.group(0), alternate_str=normalized_text)
            return 1 + int(match_tret_lau.group(1)), context
            
        return None, ''
    

    def has_mezzanine(self) -> bool:        
        if not self.text:
            return False, ''
        if (matched := self.has_mezzanine_pattern.search(self.text)):
            context = self.pattern_match_surroundings(matched.group(0))
            return True, context
        else:
            return False, ''


    def front_road_width(self) -> None|float:
        if not self.text:
            return None, ''
        
        values_contexts = [(
            float(m.group(1).replace(',', '.')),
            self.pattern_match_surroundings(m.group(0))
        ) for m in self.front_road_width_pattern.finditer(self.text)]
        
        return max(values_contexts) if values_contexts else (None, '')
    

    def facing_direction(self) -> None|Literal['đông', 'tây', 'nam', 'bắc', 'đông nam', 'đông bắc', 'tây nam', 'tây bắc']:
        if not self.text:
            return None, ''
        normalized_text = self.text.replace('-','').replace(':','')
        
        matched = self.facing_direction_patterns['find_direction'].search(normalized_text)
        if not matched:
            return None, ''
        context = self.pattern_match_surroundings(matched.group(0), alternate_str=normalized_text)
        if re.search(self.facing_direction_patterns['house_direction_validator'], matched.group(0)) or not re.search(r'ban\s*công', context):
            direction = re.sub(r'\s+', ' ' ,matched.group(1)).strip()
            return direction, context
        
        return None, ''
    

    def balcony_direction(self) -> None|Literal['đông', 'tây', 'nam', 'bắc', 'đông nam', 'đông bắc', 'tây nam', 'tây bắc']:
        if not self.text:
            return None, ''
        normalized_text = self.text.replace('-','').replace(':','')
        
        matched = self.balcony_direction_pattern.search(normalized_text)
        if not matched:
            return None, ''
        context = self.pattern_match_surroundings(matched.group(0), alternate_str=normalized_text)
        direction = re.sub(r'\s+', ' ' ,matched.group(1)).strip()
        return direction, context
        

    def front_width(self) -> None|float:           
        if not self.text:
            return None, ''

        # dimensions pattern: 8m x 12m
        dimensions_matches = list(self.front_width_patterns['dimensions'].finditer(self.text))
        if len(dimensions_matches) > 1:
            context = ' 🦑 '.join([self.pattern_match_surroundings(m.group(0)) for m in dimensions_matches])
            unique_values_matched = [float(m.group(1).replace(',', '.')) for m in dimensions_matches]
            if len(set(unique_values_matched)) == 1:
                return unique_values_matched[0], context
            else:
                if self.verbose:
                    print(">1 unique front_width matched, ignoring all")
                return None, context
        elif len(dimensions_matches) == 1:
            context = self.pattern_match_surroundings(dimensions_matches[0].group(0))
            return float(dimensions_matches[0].group(1).replace(',', '.')), context

        # keyword based: mặt tiền/ngang 8m
        matches = list(self.front_width_patterns['keywords'].finditer(self.text))
        if matches:
            values_contexts = [(
                float(m.group(1).replace(',', '.')),
                self.pattern_match_surroundings(m.group(0))
            ) for m in matches]
            
            return max(values_contexts) if values_contexts else (None, '')


        # edge case: 8m mặt đường/8m giáp đường
        matches = list(self.front_width_patterns['edge_case'].finditer(self.text))
        if matches:
            values_contexts = [(
                float(m.group(1).replace(',', '.')),
                self.pattern_match_surroundings(m.group(0))
            ) for m in matches]
            
            return max(values_contexts) if values_contexts else (None, '')

        return None, ''


    def extract(self, subset: list[str]|None = None, include_context:bool=False) -> dict:
        try:
            results = {}
            for key in (subset if subset else self.EXTRACT_FUNCS):
                func = getattr(self, key, None)
                if not callable(func):
                    results[f"ex_{key}"] = None
                    if self.context_r > 1:
                        results[f"ex_{key}_context"] = ""
                    continue

                value, context = func()
                results[f"ex_{key}"] = value
                if include_context:
                    results[f"ex_{key}_context"] = context
            return results
        except Exception as e:
            if self.verbose:
                print(e)
            results = {}
            for key in (subset if subset else self.EXTRACT_FUNCS):
                results[f"ex_{key}"] = None
                if include_context:
                    results[f"ex_{key}_context"] = ""
            return results
        

    def pattern_match_surroundings(self, pattern_match:str, alternate_str:str=None) -> str:
        if not alternate_str:
            text = self.text
        else:
            text = alternate_str

        start_pos = text.find(pattern_match)
        if start_pos == -1:
            return ''
        end_pos = start_pos + len(pattern_match)
        if self.context_r >= 0:
            return text[max(0, start_pos - self.context_r): min(len(text), end_pos + self.context_r + 1)]
        else:
            return ''


def test_extraction_bulk(df:pd.DataFrame, extract_src_col:str, target_cols:List[str]=[], n_tests:int = 200, context_r:int = -1, only_na_target:bool=False) -> pd.DataFrame:
    cols_in_df = [col for col in target_cols if col in df.columns]
    if not cols_in_df:
        test_set = df.loc[df[extract_src_col].notna(), extract_src_col].to_frame()
    else:
        if only_na_target:
            #use any(axis=1) or all(axis=1) to avoid expensive element-wise alignment & large intermediate boolean (faster)
            test_set = df.loc[(df[extract_src_col].notna()) & (df[cols_in_df].isna().any(axis=1)), [extract_src_col] + cols_in_df]
        else:
            test_set = df.loc[df[extract_src_col].notna(), [extract_src_col] + cols_in_df]
    test_set = test_set.sample(min(n_tests, len(test_set))).copy()

    extracted_data = []
    for text in tqdm(test_set[extract_src_col], desc="Extracting info"):
        extractor = PropertyInfoExtractor(text, context_r = context_r, verbose=True)
        extracted_data.append(extractor.extract(subset=target_cols, include_context=True))
    extracted_df = pd.DataFrame(extracted_data)

    if context_r >= 1 and len(target_cols) > 1:
        result_df = pd.concat([extracted_df, test_set.reset_index(drop=True)], axis=1)
    else:
        result_df = pd.concat([test_set.reset_index(drop=True), extracted_df], axis=1)      # swap data
    if only_na_target and not cols_in_df:
        result_df.drop(columns=cols_in_df)

    return result_df

def test_extraction_TC(mode:str, test_cases:List[str], context_r=25) -> pd.DataFrame:
    results = []
    for test_str in test_cases:
        results.append(PropertyInfoExtractor(test_str, context_r=context_r,verbose=True).extract([mode], include_context=True).values())
    return pd.DataFrame({'test_str':test_cases, 'results': results})

def apply_extraction(df:pd.DataFrame, extract_src_col:str, targets:List[str]=[]) -> pd.DataFrame:
    # cols_in_df = [col for col in targets if col in df.columns]
    # for col in cols_in_df:
    #     texts = df.loc[(df[extract_src_col].notna()) & (df[col].isna()), extract_src_col]

    #     extracted_data = []
    #     for text in tqdm(texts, desc=f"Extracting {col}"):
    #         extractor = PropertyInfoExtractor(text, context_r = -1, verbose=False)
    #         result = extractor.extract(subset=[col], include_context=False)
    #         extracted_data.append(result[f"ex_{col}"])
    #     df.loc[(df[extract_src_col].notna()) & (df[col].isna()), col] = extracted_data
    
    # cols_new = [col for col in targets if col in df.columns]
    # for col in cols_new:
    #     texts = df.loc[df[extract_src_col].notna(), extract_src_col]

    #     extracted_data = []
    #     for text in tqdm(texts, desc=f"Extracting {col}"):
    #         extractor = PropertyInfoExtractor(text, context_r = -1, verbose=False)
    #         result = extractor.extract(subset=[col], include_context=False)
    #         extracted_data.append(result[f"ex_{col}"])
    #     df[col] = pd.NA  # Initialize new column
    #     df.loc[df[extract_src_col].notna(), col] = extracted_data

    # print("Extraction done")

    df_filled = df.copy()
    df_filled[[col for col in targets if col not in df_filled.columns]] = pd.NA
    
    for idx, row in df_filled.iterrows():
        text = row[extract_src_col]
        if pd.isna(text) or not isinstance(text, str) or not text.strip():
            continue
        
        extractor = PropertyInfoExtractor(text, context_r=-1, verbose=False)
        results = extractor.extract(include_context=False)
        
        for col in targets:
            ex_key = f"ex_{col}"
            extracted_value = results.get(ex_key)
            if pd.isna(row[col]) and extracted_value is not None:
                df_filled.at[idx, col] = extracted_value
    
    return df_filled


def text_extraction_report(df_before: pd.DataFrame, df_after: pd.DataFrame, targets:List[str]=[]):
    """
    Test the `fill_missing_from_description` function with a side-by-side comparison table:
      - Missing Before
      - Missing After
      - Values Filled
      - Fill Rate (%)
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input DataFrame with 'description' and target columns.
    description_col : str
        Name of the description column (default: 'description')
    
    Returns:
    --------
    dict: Summary including the filled DataFrame and stats.
    """
    if len(df_before) != len(df_after):
        raise ValueError('Before - After datasets have mismatched number of rows. Check your inputs')

    # Compute missing counts
    missing_before = df_before[targets].isna().sum()
    missing_after = df_after[targets].isna().sum()
    filled_counts = missing_before - missing_after
    fill_rate = (filled_counts / missing_before.replace(0, 1)) * 100  # Avoid div by zero
    
    # Create side-by-side comparison table
    comparison_df = pd.DataFrame({
        "Missing Before": [f'{n_missing_before} ({round(n_missing_before / len(df_before) * 100, 2)} %)' for n_missing_before in missing_before],
        "Missing After": [f'{n_missing_after} ({round(n_missing_after / len(df_after) * 100, 2)} %)' for n_missing_after in missing_after],
        "Missing values filled": filled_counts
    }).fillna(0)
    
    # # Add total row
    # totals = pd.DataFrame([{
    #     "Missing Before": missing_before.sum(),
    #     "Missing After": missing_after.sum(),
    #     "Filled": filled_counts.sum(),
    #     "Fill Rate (%)": (filled_counts.sum() / missing_before.sum() * 100).round(2) if missing_before.sum() > 0 else 0
    # }], index=["TOTAL"])
    
    # comparison_df = pd.concat([comparison_df, totals])
    
    return comparison_df

if __name__ ==  '__main__':
    facing_direction_tc = [
        'hướng Đông Nam',
        'hướng cửa chính: tây -bắc',
        'nhà hướng tây',
        'hướng ban công tây bắc',
        'ban công nhà hướng nam'
    ]
    print('extracting...')
    print(test_extraction_TC('facing_direction', facing_direction_tc))
    print('done')
