from collections import OrderedDict
import bokeh.models as bmd
from bokeh.palettes import Plasma256
import holoviews as hv
from holoviews.operation.datashader import datashade, dynspread
import datashader as ds
import panel as pn
import param
import functools

from figure import config
from figure.query import get_data_aiida

hv.extension('bokeh')
hv_renderer = hv.renderer('bokeh').instance(mode='server')

# Note: We are now recreating the plot every time.
# In principle it would be nice to just update the ColunmDataSource but I
# I don't think there is a way around this in holoviews (?)

plot_px = 600
dynspread.threshold = 0.6  # maximum fraction of distance to neighboring point
dynspread.max_px = 40  # resolution of dots (NOT: size)
overlay_threshold = 2000  # start showing overlay when that many points left


def filter_points(points, x_range, y_range):
    """Filter points by x/y range.

    To be used with RangeXY stream.
    """
    if x_range is None or y_range is None:
        return points
    return points[x_range, y_range]


def hover_points(points, threshold=overlay_threshold):
    """Filter points by threshold.

    Returns empty list if number of input points exceeds threshold.
    """
    if len(points) > threshold:
        return points.iloc[:0]
    return points


def prepare_data(inp_x, inp_y, inp_clr):
    """Prepare data source"""

    # query for results
    inp_list = [inp_x, inp_y, inp_clr]
    results_wnone = get_data_aiida(
        inp_list)  #returns [inp_x_value, inp_y_value, inp_clr_value, cof-id]
    # dump None lists that make bokeh crash! TODO: improve!
    results = []
    for l in results_wnone:
        if None not in l:
            results.append(l)

    # prepare data for plotting
    nresults = len(results)
    if not results:
        results = [[0, 0, 0, 'no data']]
        msg = "No matching COFs found."
    else:
        msg = "{} COFs found.".format(nresults)
        if nresults > config.max_points:
            results = results[:config.max_points]
        msg += "\nPlotting {}...".format(len(results))

    group_label, x, y, clrs = list(zip(*results))
    x = list(map(float, x))
    y = list(map(float, y))
    clrs = list(map(float, clrs))

    data = {'x': x, 'y': y, 'color': clrs, 'name': group_label}
    return data, msg


def get_hover(inp_x, inp_y, inp_clr):
    """Returns hover tool"""
    q_x = config.quantities[inp_x]
    q_y = config.quantities[inp_y]
    q_clr = config.quantities[inp_clr]
    xhover = (q_x["label"], "@x {}".format(q_x["unit"]))
    yhover = (q_y["label"], "@y {}".format(q_y["unit"]))
    if 'unit' not in list(q_clr.keys()):
        clr_val = "@color"
    else:
        clr_val = "@color {}".format(q_clr['unit'])
    tooltips = [
        ("name", "@name"),
        xhover,
        yhover,
        (q_clr["label"], clr_val),
    ]
    return bmd.HoverTool(tooltips=tooltips)


def get_plot(inp_x, inp_y, inp_clr):
    """Creates holoviews plot"""
    data, msg = prepare_data(inp_x, inp_y, inp_clr)
    source = bmd.ColumnDataSource(data=data)

    # hovering
    hover = get_hover(inp_x, inp_y, inp_clr)

    # tap
    tap = bmd.TapTool()
    tap.callback = bmd.OpenURL(url="detail?id=@name")

    # plot
    points = hv.Points(
        source.data,
        kdims=['x', 'y'],
        vdims=['color', 'name'],
    )
    filtered = points.apply(filter_points,
                            streams=[hv.streams.RangeXY(source=points)])

    p_shaded = datashade(
        filtered,
        width=plot_px,
        height=plot_px,
        cmap=Plasma256,
        aggregator=ds.mean('color')  # we want color of mean value under pixel
    )
    p_hover = filtered.apply(hover_points)

    update_fn = functools.partial(update_legends,
                                  inp_x=inp_x,
                                  inp_y=inp_y,
                                  inp_clr=inp_clr)
    hv_plot = (dynspread(p_shaded) * p_hover).opts(
        hv.opts.Points(
            tools=[
                tap,
                'pan',
                'box_zoom',
                'save',
                'reset',
                hover,
            ],
            active_tools=['wheel_zoom'],
            #active_scroll='box_zoom',
            #active_drag='box_zoom',
            alpha=0.2,
            hover_alpha=0.5,
            size=10,
            width=plot_px,
            height=plot_px,
            color='color',
            cmap=Plasma256,
            colorbar=True,
            show_grid=True,
        ),
        hv.opts(toolbar='above', finalize_hooks=[update_fn]),
    )
    #     output_backend='webgl',

    p_new = hv_renderer.get_plot(hv_plot).state

    return p_new, msg


def update_legends(plot, _element, inp_x, inp_y, inp_clr):
    p = plot.state

    q_x = config.quantities[inp_x]
    q_y = config.quantities[inp_y]

    #title = "{} vs {}".format(q_x["label"], q_y["label"])
    xlabel = "{} [{}]".format(q_x["label"], q_x["unit"])
    ylabel = "{} [{}]".format(q_y["label"], q_y["unit"])

    q_clr = config.quantities[inp_clr]
    if 'unit' not in list(q_clr.keys()):
        clr_label = q_clr["label"]
    else:
        clr_label = "{} [{}]".format(q_clr["label"], q_clr["unit"])

    p.xaxis.axis_label = xlabel
    p.yaxis.axis_label = ylabel

    p.title_location = 'right'
    p.title.align = 'center'
    p.title.text_font_size = '10pt'
    p.title.text_font_style = 'italic'
    p.title.text = clr_label


pn.extension()
plot_dict = OrderedDict(
    ((config.quantities[q]['label'], q) for q in config.quantities))


class StructurePropertyVisualizer(param.Parameterized):

    x = param.Selector(objects=plot_dict,
                       default='henry_coefficient_average_ht')
    y = param.Selector(objects=plot_dict, default='PE')
    clr = param.Selector(objects=OrderedDict(plot_dict),
                         default='Channels.Largest_free_spheres.0')
    msg = pn.pane.HTML("")
    _plot = None  # reference to current plot

    @param.depends('x', 'y', 'clr')
    def plot(self):
        selected = [self.x, self.y, self.clr]
        unique = set(selected)
        if len(unique) < len(selected):
            self.msg.object = "<b style='color:red;'>Warning: {} contains duplicated selections.</b>".format(
                ", ".join([config.quantities[s]['label'] for s in selected]))
            return self._plot

        self._plot, self.msg.object = get_plot(self.x, self.y, self.clr)
        return self._plot


explorer = StructurePropertyVisualizer()

gspec = pn.GridSpec(sizing_mode='stretch_both', max_width=900)
gspec[0, 0] = explorer.param
gspec[:2, 1:4] = explorer.plot
gspec[1, 0] = explorer.msg

gspec.servable()
