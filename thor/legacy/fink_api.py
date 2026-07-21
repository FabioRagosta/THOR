from thor.brokers.client import BrokerClient
from thor.exception import BrokerError
import time
import pandas as pd
import logging

logger = logging.getLogger(__name__)
# -----------------------------------------------------------------------------
# FINK Broker Functions
# -----------------------------------------------------------------------------
import requests


class FinkAPI:
    _URLS = {
        'ztf': {
            'base': 'https://api.ztf.fink-portal.org',
            'portal': 'https://ztf.fink-portal.org',
            'docs': 'https://ztf.fink-portal.org/docs',
        },
        'lsst': {
            'base': 'https://api.lsst.fink-portal.org/',
            'portal': 'https://lsst.fink-portal.org',
            'docs': 'https://doc.lsst.fink-broker.org',
        }
    }
 
    _ML_CLASSIFIERS = {
        'snn_sn_vs_all': 'Siamese Neural Network (SN vs all)',
        'rf_snia_vs_nonia': 'Random Forest (SN Ia vs non-Ia)',
        'snn_snia_vs_nonia': 'Siamese Neural Network (SN Ia vs non-Ia)',
        'rf_kn_vs_nonkn': 'Random Forest (Kilonova vs non-KN)',
    }
 
    _ZTF_LATEST_CLASSES = [
        'Supernova', 'SN', 'SNIa', 'SNIax', 'SNIb', 'SNIc', 'SNII',
        'AGN', 'Kilonova', 'Unknown', 'Microlens', 'TDE', 'CV',
    ]
 
    _LSST_REGIONS = [
        (53.0,   -27.5, 300, "COSMOS/Fornax Deep"),
        (150.12,  2.21, 300, "COSMOS Field"),
        (34.5,   -5.17, 300, "XMM-LSS"),
        (53.1,  -28.1,  300, "ECDF-S"),
        (10.0,  -45.0,  300, "Wide Field South"),
    ]
    # -------------------------------------------------------------------------
 
    def __init__(self, survey='ztf', timeout=30, max_retries=3, verify_ssl=None):
        self.survey = survey.lower()
        self.timeout = timeout
        self.max_retries = max_retries
        
        if verify_ssl is None:
            self.verify_ssl = (self.survey == 'lsst')
        else:
            self.verify_ssl = verify_ssl
 
        if self.survey not in self._URLS:
            raise ValueError(f"Survey '{survey}' not supported. Use 'ztf' or 'lsst'")
 
        self.base_url = self._URLS[self.survey]['base']
        self.portal_url = self._URLS[self.survey]['portal']
        self.docs_url = self._URLS[self.survey]['docs']
 
        self.headers = {
            'User-Agent': 'SNHunter/1.0 (FINK Client)',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
 
        #self.client = BrokerClient(
        #    timeout=timeout,
        #    retries=max_retries,
        #)
        
        #self.client.session.headers.update(self.headers)
        self.session = requests.Session()

        self.session.headers.update(self.headers)
        
        self.session.verify = self.verify_ssl
        
        self._log_init()
 
    def _log_init(self):
        logger.info(f"\n  🔭 FINK Client initialized:")
        logger.info(f"     Survey: {self.survey.upper()}")
        logger.info(f"     API URL: {self.base_url}")
        logger.info(f"     Portal: {self.portal_url}")
       
    def _make_request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}{endpoint}"
 
        if 'verify' not in kwargs:
            kwargs['verify'] = self.verify_ssl
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout 
        for attempt in range(self.max_retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, **kwargs)
                else:
                    response = self.session.post(url, **kwargs)
 
                if response.status_code == 502:
                    print(f"      ⚠️ FINK {self.survey.upper()} temporarily unavailable (502), "
                          f"attempt {attempt + 1}/{self.max_retries}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
 
                response.raise_for_status()
                return response
 
            except requests.exceptions.SSLError as e:
                print(f"      ⚠️ SSL Error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                    continue
                return None
 
            except requests.exceptions.Timeout:
                print(f"      ⚠️ Timeout, attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                    continue
                return None
 
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    print(f"      ❌ Request error: {e}")
                    return None
                time.sleep(2)
                continue
 
        return None
     
    def _safe_float(self, value, default=None):
        try:
            if pd.isna(value):
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    def get_object(self, object_id):
        """
        Retrieve one object from Fink.
    
        Parameters
        ----------
        object_id : str
    
        Returns
        -------
        pandas.DataFrame
        """
    
        result = self._make_request(
            "POST",
            "/api/v1/objects",
            json={
                "objectId": object_id,
                "output-format": "json",
            },
        )
    
        df = pd.DataFrame(result)
    
        if df.empty:
            return df
    
        df = self._normalize_columns(df)
        df = self._apply_classification_hierarchy(df)
    
        return df
        
    def lightcurve(self, object_id):
        """
        Return the complete light curve.
    
        Parameters
        ----------
        object_id : str
    
        Returns
        -------
        pandas.DataFrame
        """
    
        return self.get_object(object_id)
    
    def classifications(self, object_id):
        """
        Return all Fink classification probabilities.
    
        Parameters
        ----------
        object_id : str
    
        Returns
        -------
        dict
        """
    
        df = self.get_object(object_id)
    
        if df.empty:
            return {}
    
        row = df.iloc[0]
    
        probabilities = {}
    
        for col in df.columns:
    
            if not col.startswith("v:"):
                continue
    
            value = row[col]
    
            if pd.isna(value):
                continue
    
            try:
                probabilities[col[2:]] = float(value)
            except Exception:
                continue
    
        return probabilities
    def query_by_classifier(self, classifier='rf_snia_vs_nonia', 
                           probability_threshold=0.5, n=100):
        """
        Query FINK using ML classifier scores (MORE RELIABLE than latests endpoint).
        
        Parameters:
        -----------
        classifier : str
            One of: 'rf_snia_vs_nonia', 'snn_sn_vs_all', 'snn_snia_vs_nonia'
        probability_threshold : float
            Minimum probability threshold (0.5-0.7 recommended)
        n : int
            Maximum number of objects to return
        """
        if classifier not in self._ML_CLASSIFIERS:
            logger.info(f"      ⚠️ Unknown classifier: {classifier}")
            logger.info(f"      Available: {list(self._ML_CLASSIFIERS.keys())}")
            return pd.DataFrame()
        
        logger.info(f"      🔍 Querying by ML classifier: {classifier} (threshold={probability_threshold})")
        
        endpoint = "/api/v1/objects"
        payload = {
            'classifier': classifier,
            'probability': probability_threshold,
            'n': n,
            'output-format': 'json',
        }
        
        response = self._make_request('POST', endpoint, json=payload)
        
        if response is None:
            return pd.DataFrame()
        
        try:
            df = pd.read_json(io.BytesIO(response.content))
            if not df.empty:
                df['query_classifier'] = classifier
                df['classifier_score'] = probability_threshold
                df['survey'] = self.survey
                df = self._normalize_columns(df)
                logger.info(f"         ✅ Found {len(df)} objects")
            return df
        except Exception as e:
            logger.info(f"         ❌ Parse error: {e}")
            return pd.DataFrame()
    def query_lsst_early_sn_candidates(self, mag_cut=27, ndet_min=3, n=200):
        """
        Query LSST FINK for early SN candidates using Active Learning filter.
        
        According to FINK documentation, the 'early_sn_candidates' filter
        achieves 86% purity on real data.
        
        Parameters:
        -----------
        mag_cut : float
            Magnitude cut (LSST 5-sigma depth ~21.5 in r-band initially)
        ndet_min : int
            Minimum number of detections
        n : int
            Maximum number of objects to return
        """
        if self.survey != 'lsst':
            logger.info(f"      ⚠️ LSST query only available for LSST survey")
            return pd.DataFrame()
        
        logger.info(f"      🔍 LSST: Querying early SN candidates (Active Learning filter)")
        logger.info(f"         Magnitude cut: {mag_cut}, Min detections: {ndet_min}")
        
        # [FIX-5] Use the early_sn_candidates filter
        endpoint = "/api/v1/lsst/objects"
        payload = {
            'filter': 'early_sn_candidates',  # Active Learning filter (86% purity)
            'mag_cut': mag_cut,
            'ndet_min': ndet_min,
            'n': n,
            'output-format': 'json',
        }
        
        response = self._make_request('POST', endpoint, json=payload)
        
        if response is None:
            return pd.DataFrame()
        
        try:
            df = pd.read_json(io.BytesIO(response.content))
            if not df.empty:
                df['query_filter'] = 'early_sn_candidates'
                df['survey'] = self.survey
                df = self._normalize_columns(df)
                
                # [FIX-8] LSST 5-sigma detection requirement
                if 'snr' in df.columns:
                    original_len = len(df)
                    df = df[df['snr'] >= 5]
                    if len(df) < original_len:
                        logger.info(f"         Filtered {original_len - len(df)} objects with SNR < 5")
                
                logger.info(f"         ✅ Found {len(df)} LSST early SN candidates")
            return df
        except Exception as e:
            logger.info(f"         ❌ Parse error: {e}")
            return pd.DataFrame()
    

    def _apply_classification_hierarchy(self, df):
        """
        Apply FINK's classification hierarchy:
        1. SIMBAD match (most reliable)
        2. Filter classification (sn_candidates, early_sn_candidates)
        3. ML classifier scores
        4. Default (Unknown)
        """
        if df.empty:
            return df
        
        # Initialize classification column
        df['classification_priority'] = 4  # 1=highest, 4=lowest
        df['classification_source'] = 'unknown'
        
        # Level 1: SIMBAD matches (most reliable)
        if 'cdsxmatch' in df.columns:
            simbad_sn = df['cdsxmatch'].str.contains('SN|Supernova', case=False, na=False)
            df.loc[simbad_sn, 'classification_priority'] = 1
            df.loc[simbad_sn, 'classification_source'] = 'SIMBAD'
        
        # Level 2: Filter classifications
        if 'fink_filter' in df.columns:
            filter_sn = df['fink_filter'] == 'sn_candidates'
            df.loc[filter_sn & (df['classification_priority'] > 2), 'classification_priority'] = 2
            df.loc[filter_sn & (df['classification_priority'] == 2), 'classification_source'] = 'filter:sn_candidates'
            
            filter_early = df['fink_filter'] == 'early_sn_candidates'
            df.loc[filter_early & (df['classification_priority'] > 2), 'classification_priority'] = 2
            df.loc[filter_early & (df['classification_priority'] == 2), 'classification_source'] = 'filter:early_sn_candidates'
        
        # Level 3: ML classifier scores
        ml_score_cols = ['snn_score', 'rf_score', 'snn_snia_score']
        for col in ml_score_cols:
            if col in df.columns:
                high_ml = df[col] > 0.7
                df.loc[high_ml & (df['classification_priority'] > 3), 'classification_priority'] = 3
                df.loc[high_ml & (df['classification_priority'] == 3), 'classification_source'] = f'ML:{col}'
        
        return df
    def cone_search(self, ra, dec, radius_arcsec=60.0, n=100):
        logger.info(f"      🔍 Cone search: RA={ra:.3f}, DEC={dec:.3f}, "
              f"radius={radius_arcsec:.1f} arcsec")
 
        endpoint = "/api/v1/conesearch"
        payload = {
            'ra': ra,
            'dec': dec,
            'radius': radius_arcsec,
            'n': n,
            'output-format': 'json',
        }
 
        response = self._make_request('POST', endpoint, json=payload)
 
        if response is None:
            return pd.DataFrame()
 
        try:
            df = pd.read_json(io.BytesIO(response.content))
            if not df.empty:
                df['query_ra'] = ra
                df['query_dec'] = dec
                df['survey'] = self.survey
                logger.info(f"         ✅ Found {len(df)} objects")
                df = self._normalize_columns(df)
            return df
        except Exception as e:
            logger.info(f"         ❌ Parse error: {e}")
            return pd.DataFrame()
 
    def query_latest_ztf(self, class_name='Supernova', n=10):
        if self.survey != 'ztf':
            logger.info(f"      ⚠️ query_latest only available for ZTF")
            return pd.DataFrame()
 
        endpoint = "/api/v1/latests"
        payload = {
            'class': class_name,
            'n': n,
            'output-format': 'json',
        }
 
        response = self._make_request('POST', endpoint, json=payload)
 
        if response is None:
            return pd.DataFrame()
 
        try:
            df = pd.read_json(io.BytesIO(response.content))
            if not df.empty:
                df['query_class'] = class_name
                df['survey'] = self.survey
                df = self._normalize_columns(df)
                logger.info(f"         ✅ Found {len(df)} objects for class {class_name}")
            return df
        except Exception as e:
            logger.info(f"         ❌ Error parsing response: {e}")
            return pd.DataFrame()
 
    def cone_search_lsst_regions(self, class_name='SN', n=50, days_back=7):
        if self.survey != 'lsst':
            return pd.DataFrame()
 
        all_objects = []
        n_per_region = max(1, n // len(self._LSST_REGIONS))
 
        for ra, dec, radius, region_name in self._LSST_REGIONS:
            df = self.cone_search(ra, dec, radius_arcsec=radius, n=n_per_region)
 
            if not df.empty:
                df['region'] = region_name
                df['query_class'] = class_name
                all_objects.append(df)
                logger.info(f"         ✅ {region_name}: {len(df)} objects")
            time.sleep(1)
 
        if all_objects:
            df_all = pd.concat(all_objects, ignore_index=True)
            df_all = df_all.drop_duplicates(subset='objectId', keep='first')
            logger.info(f"      📊 Total unique objects: {len(df_all)}")
            return df_all
        return pd.DataFrame()
 
    def _normalize_columns(self, df):
        if df.empty:
            return df
 
        if self.survey == 'ztf':
            column_map = {
                'i:objectId': 'objectId', 'd:objectId': 'objectId',
                'i:ra': 'ra', 'i:dec': 'dec',
                'i:ndethist': 'ndet',
                'i:magpsf': 'magpsf', 'i:sigmapsf': 'magerr',
                'd:snn_sn_vs_all': 'snn_score',
                'd:snn_snia_vs_nonia': 'snn_snia_score',
                'd:rf_snia_vs_nonia': 'rf_score',
                'd:rf_kn_vs_nonkn': 'kn_score',
                'd:rf_agn_vs_nonagn': 'agn_score',
                'd:mulens': 'microlens_score',
                'd:cdsxmatch': 'classification',
                'd:roid': 'is_sso',
            }
            for col in df.columns:
                if col.startswith('i:') and col not in column_map:
                    column_map[col] = col.replace('i:', '')
                elif col.startswith('d:') and col not in column_map:
                    column_map[col] = col.replace('d:', '')
        else:
            column_map = {
                'r:diaObjectId': 'objectId', 'diaObjectId': 'objectId',
                'r:ra': 'ra', 'r:dec': 'dec',
                'r:nDiaSources': 'ndet',
                'r:psfFlux': 'magpsf', 'r:psfFluxErr': 'magerr',
                'f:clf_snnSnVsOthers_score': 'snn_score',
                'f:clf_earlySNIa_score': 'early_snia_score',
                'f:clf_cats_score': 'cats_score',
                'f:main_label_classifier': 'classification',
                'f:main_label_crossmatch': 'crossmatch_class',
                'f:clf_cats_class': 'cats_class',
            }
            for col in df.columns:
                if (col.startswith('r:') or col.startswith('f:')) and col not in column_map:
                    column_map[col] = col.replace('r:', '').replace('f:', '')
 
        df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
 
        prob_cols = []
        if self.survey == 'ztf':
            for col in ['snn_score', 'rf_score']:
                if col in df.columns:
                    prob_cols.append(col)
        else:
            for col in ['snn_score', 'cats_score', 'early_snia_score']:
                if col in df.columns:
                    prob_cols.append(col)
 
        if prob_cols and 'sn_probability' not in df.columns:
            df['sn_probability'] = 1 - df[prob_cols].max(axis=1)
        elif 'sn_probability' not in df.columns:
            if 'classification' in df.columns:
                def class_to_score(classification):
                    if pd.isna(classification):
                        return 0.0
                    class_str = str(classification).upper()
                    if any(keyword in class_str for keyword in ['SN', 'SUPERNOVA', 'SN_NEAR_GALAXY', 
                                                                  'EXTRAGALACTIC_NEW', 'EXTRAGALACTIC_LT20MAG',
                                                                  'IN_TNS', 'HOSTLESS', 'UNIFORM_SAMPLE']):
                        return 0.8
                    elif 'AGN' in class_str:
                        return 0.3
                    elif 'GALAXY' in class_str:
                        return 0.2
                    elif 'STAR' in class_str:
                        return 0.1
                    else:
                        return 0.2
                df['sn_probability'] = df['classification'].apply(class_to_score)
            else:
                df['sn_probability'] = 0.5
 
        if 'ndet' in df.columns:
            df['ndet'] = pd.to_numeric(df['ndet'], errors='coerce').fillna(0).astype(int)
 
        for coord in ['ra', 'dec']:
            if coord in df.columns:
                df[coord] = df[coord].apply(lambda x: self._safe_float(x))
 
        return df
    @property
    def name(self):
    
        return "Fink"
    @property
    def survey_name(self):
    
        return self.survey
    def close(self):

        self.client.close()