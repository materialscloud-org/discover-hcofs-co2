from __future__ import absolute_import
import collections
import yaml
from os.path import join, dirname

static_dir = join(dirname(__file__), "static")

with open(join(static_dir, "columns.yml"), 'r') as f:
    quantity_list = yaml.load(f, Loader=yaml.SafeLoader)

for item in quantity_list:
    if 'scale' not in item.keys():
        item['scale'] = 'linear'

quantities = collections.OrderedDict([(q['column'], q) for q in quantity_list])

geometric_quantities = {
    k: quantities[k]
    for k in [
        'Density', 'Channels.Largest_included_spheres.0',
        'Channels.Largest_free_spheres.0', 'AV_Volume_fraction'
    ]
}

plot_quantities = [
    q for q in quantities.keys() if quantities[q]['type'] == 'float'
]

with open(join(static_dir, "filters.yml"), 'r') as f:
    filter_list = yaml.load(f, Loader=yaml.SafeLoader)

with open(join(static_dir, "presets.yml"), 'r') as f:
    presets = yaml.load(f, Loader=yaml.SafeLoader)

for k in presets.keys():
    if 'clr' not in list(presets[k].keys()):
        presets[k]['clr'] = presets['default']['clr']

max_points = 70000
