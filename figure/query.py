"""Querying the DB
"""
from __future__ import absolute_import
from bokeh.models.widgets import RangeSlider, CheckboxButtonGroup
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
    """Query the AiiDA database: find info in the README."""
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm import Node, Dict, Group, CifData

    filters = {}

    qb = QueryBuilder()
    qb.append(Group, filters={ 'label': {'like': 'group_%'} }, tag='group')
    qb.append(CifData, with_group='group', filters={'extras.group_tag': 'orig_cif'},
        project=['label'])

    for inp in inp_list:
        if 'henry_coefficient_average' in inp:
            proj = 'henry_coefficient_average' # take out _co2, _n2, _ht
        else:
            proj = inp
        qb.append(Dict, with_group='group', filters={'extras.group_tag': get_tag[inp]},
            project=['attributes.{}'.format(proj)])

    return qb.all()
