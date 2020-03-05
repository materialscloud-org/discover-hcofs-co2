"""Querying the DB
"""
from __future__ import absolute_import
import os
from aiida import load_profile
from aiida.orm.querybuilder import QueryBuilder
from aiida.orm import Dict, Group, CifData
import pandas as pd
from figure import config

load_profile()

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_GEO = os.path.join(THIS_DIR, 'cache_geo.pkl')
CACHE_ALL = os.path.join(THIS_DIR, 'cache_all.pkl')

# pylint: disable=too-many-locals
data_empty = dict(x=[0], y=[0], uuid=['1234'], color=[0], name=['no data'])

get_tag = {
    'PE': 'pe_out',
    'WCg': 'pe_out',
    'WCv': 'pe_out',
    'Pur': 'pe_out',
    'Density': 'ht_geom_out',
    'Channels.Largest_included_spheres.0': 'ht_geom_out',
    'Channels.Largest_free_spheres.0': 'ht_geom_out',
    'AV_Volume_fraction': 'ht_geom_out',
    'henry_coefficient_average_ht': 'ht_kh_out2',
    'henry_coefficient_average_co2': 'isot_co2_out',
    'henry_coefficient_average_n2': 'isot_n2_out',
    'POAV_Volume_fraction': 'isot_co2_out',
    'POAV_cm^3/g': 'isot_co2_out',
}


def get_data_aiida(inp_list):
    """Query the AiiDA database: find info in the README.
    
    Note: Removing the group filter speeds up queries on 70k COFs from ~10s to ~1s.
    """

    qb = QueryBuilder()
    qb.append(Group, filters={'label': {'like': 'group_%'}}, tag='group')
    qb.append(CifData,
              with_group='group',
              filters={'extras.group_tag': 'orig_cif'},
              project=['uuid', 'label'])

    for inp in inp_list:
        if 'henry_coefficient_average' in inp:
            proj = 'henry_coefficient_average'  # take out _co2, _n2, _ht
        else:
            proj = inp
        qb.append(Dict,
                  with_group='group',
                  filters={'extras.group_tag': get_tag[inp]},
                  project=['attributes.{}'.format(proj)])

    return qb.all()


def populate_cache():
    """Cache queries needed for figure.

    Creates one cache for structures with geometric features only,
    and one cache for structures with all features.
    """
    all_labels = list(config.quantities)
    all_qs = get_data_aiida(all_labels)
    df = pd.DataFrame(all_qs, columns=['uuid', 'label'] + all_labels)
    df.to_pickle(CACHE_ALL)

    geo_labels = list(config.geometric_quantities)
    geo_qs = get_data_aiida(geo_labels)
    df = pd.DataFrame(geo_qs, columns=['uuid', 'label'] + geo_labels)
    df.to_pickle(CACHE_GEO)


def get_data_cache(inp_list):
    if not os.path.isfile(CACHE_GEO) or not os.path.isfile(CACHE_ALL):
        populate_cache()

    if set(inp_list).issubset(set(config.geometric_quantities)):
        df = pd.read_pickle(CACHE_GEO)
    else:
        df = pd.read_pickle(CACHE_ALL)

    data = df[['uuid', 'label'] + inp_list]
    print(data)

    return data.dropna().to_numpy()
