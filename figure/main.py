from aiida import load_profile
load_profile()
import config
import bokeh.models as bmd

import holoviews as hv
from holoviews.operation.datashader import datashade

hv.extension('bokeh')
hv_renderer = hv.renderer('bokeh').instance(mode='server')

# todo: currently we are recreating the plot every time
# instead we could store a reference to the ColumnDataSource in cache and just update that
# (as long as no switch between cbar types)
# Look into what the performance benefit of this would be; also whether it is compatible with panel


def filter_points(points, x_range, y_range):
    """Filter points by x/y range.

    To be used with RangeXY stream.
    """
    if x_range is None or y_range is None:
        return points
    return points[x_range, y_range]

def hover_points(points, threshold=5000):
    """Filter points by threshold.

    Returns empty list if number of input points exceeds threshold.
    """
    if len(points) > threshold:
        return points.iloc[:0]
    return points

def prepare_data(inp_x, inp_y, inp_clr):
    #TODO: For performance, consider reusing p_old (i.e. just updating its .data source)

    # query for results
    from figure.query import get_data_aiida 
    inp_list = [inp_x, inp_y, inp_clr]
    results_wnone = get_data_aiida(inp_list) #returns [inp_x_value, inp_y_value, inp_clr_value, cof-id]
    # dump None lists that make bokeh crash! TODO: improve!
    results = []
    for l in results_wnone:
        if not None in l:
            results.append(l)

    # prepare data for plotting
    nresults = len(results)
    if not results:
        results = [ [0,0,0,'no data'] ]
        msg = "No matching COFs found."     
    else:
        msg = "{} COFs found.".format(nresults)
        if nresults > config.max_points:
            results = results[:config.max_points]    
        msg += "\nPlotting {}...".format(len(results))

    group_label, x, y, clrs = zip(*results)
    x = list(map(float, x))
    y = list(map(float, y))
    clrs = list(map(float, clrs))

    data = {
        'x': x,
        'y': y,
        'color': clrs,
        'name': group_label
    }
    return data, msg


def get_plot(inp_x, inp_y, inp_clr):
    #TODO: For performance, consider reusing p_old (i.e. just updating its .data source)

    data, msg = prepare_data(inp_x, inp_y, inp_clr)
    
    # create bokeh plot
    import bokeh.plotting as bpl
    from bokeh.palettes import Plasma256

    plot_px = 600
    hover = bmd.HoverTool(tooltips=[])
    tap = bmd.TapTool()


    source = bmd.ColumnDataSource(data = data)
    points = hv.Points(source.data, kdims=['x','y'], vdims=['color'])
    filtered = points.apply(filter_points, streams=[hv.streams.RangeXY(source=points)])
    
    p_shaded = datashade(filtered, width=plot_px, height=plot_px)
    p_hover = filtered.apply(hover_points)

    hv_plot = (p_shaded * p_hover.opts(
           tools=['hover', tap], active_tools=['wheel_zoom'],
           alpha=0.1, hover_alpha=0.2, size=10,
          width=600, height=700,
    ))

    p_new = hv_renderer.get_plot(hv_plot).state
    #p_new = hv.render(hv_plot)


    
    # # Todo: If possible, setting the axis scale should be moved to "update_legends"
    # q_x = config.quantities[inp_x]
    # q_y = config.quantities[inp_y]

    # p_new = bpl.figure(
    #     plot_height=plot_px,
    #     plot_width=plot_px,
    #     toolbar_location='above',
    #     tools=[
    #         'pan',
    #         'wheel_zoom',
    #         'box_zoom',
    #         'save',
    #         'reset',
    #         hover,
    #         tap,
    #     ],
    #     #active_scroll='box_zoom',
    #     active_drag='box_zoom',
    #     output_backend='webgl',
    #     title='',
    #     title_location='right',
    #     x_axis_type=q_x['scale'],
    #     y_axis_type=q_y['scale'],
    # )
    # p_new.title.align = 'center'
    # p_new.title.text_font_size = '10pt'
    # p_new.title.text_font_style = 'italic'
    
    # update_legends(p_new, inp_x, inp_y, inp_clr, hover, tap)
    
    # cmap = bmd.LinearColorMapper(palette=Plasma256)
    # fill_color = {'field': 'color', 'transform': cmap}
    # p_new.circle('x', 'y', size=10, source=source, fill_color=fill_color)
    # cbar = bmd.ColorBar(color_mapper=cmap, location=(0, 0))
    # #cbar.color_mapper = bmd.LinearColorMapper(palette=Viridis256)
    # p_new.add_layout(cbar, 'right')
    
    return p_new, msg


# In[ ]:


def update_legends(p, inp_x, inp_y, inp_clr, hover, tap):

    q_x = config.quantities[inp_x]
    q_y = config.quantities[inp_y]

    #title = "{} vs {}".format(q_x["label"], q_y["label"])
    xlabel = "{} [{}]".format(q_x["label"], q_x["unit"])
    ylabel = "{} [{}]".format(q_y["label"], q_y["unit"])
    xhover = (q_x["label"], "@x {}".format(q_x["unit"]))
    yhover = (q_y["label"], "@y {}".format(q_y["unit"]))

    q_clr = config.quantities[inp_clr]
    if 'unit' not in q_clr.keys():
        clr_label = q_clr["label"]
        clr_val = "@color"
    else:
        clr_val = "@color {}".format(q_clr['unit'])
        clr_label = "{} [{}]".format(q_clr["label"], q_clr["unit"])
    
    hover.tooltips = [
        ("name", "@name"),
        xhover,
        yhover,
        (q_clr["label"], clr_val),
    ]


    q_clr = config.quantities[inp_clr]
    clr_label = "{} [{}]".format(q_clr["label"], q_clr["unit"])
    hover.tooltips = [
        ("name", "@name"),
        xhover,
        yhover,
        (q_clr["label"], "@color {}".format(q_clr["unit"])),
    ]

    p.xaxis.axis_label = xlabel
    p.yaxis.axis_label = ylabel
    p.title.text = clr_label

    url = "detail?id=@name"
    tap.callback = bmd.OpenURL(url=url)


# In[ ]:


import panel as pn
import param
import config
from collections import OrderedDict

pn.extension()
plot_dict = OrderedDict( ((config.quantities[q]['label'], q) for q in config.quantities) )

class StructurePropertyVisualizer(param.Parameterized):
    
    x = param.Selector(objects=plot_dict, default='henry_coefficient_average_ht')
    y = param.Selector(objects=plot_dict, default='PE')
    clr = param.Selector(objects=OrderedDict(plot_dict), default='Channels.Largest_free_spheres.0')
    msg = pn.pane.HTML("")
    _plot = None  # reference to current plot
    
    @param.depends('x', 'y', 'clr')
    def plot(self):
        selected = [self.x, self.y, self.clr]
        unique = set(selected)
        if len(unique) < len(selected):
            self.msg.object = "<b style='color:red;'>Warning: {} contains duplicated selections.</b>".format(", ".join([config.quantities[s]['label'] for s in selected]))
            return self._plot
        
        self._plot, self.msg.object = get_plot(self.x, self.y, self.clr)
        return self._plot

explorer = StructurePropertyVisualizer()

gspec = pn.GridSpec(sizing_mode='stretch_both', max_width=900)
gspec[0, 0] = explorer.param
gspec[:2, 1:4] = explorer.plot
gspec[1, 0] = explorer.msg

gspec.servable()

