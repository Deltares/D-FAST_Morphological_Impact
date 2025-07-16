from typing import Optional, Any
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
import shapely.plotting 
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap
from matplotlib import ticker
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from shapely import LineString
import xarray as xr
from xarray import DataArray
import xugrid as xu
from dfastmi.batch.plotting import chainage_markers, savefig
from dfastmi.batch.PlotOptions import PlotOptions
from dfastrbk.src.batch import operations
from dfastrbk.src.kernel import flow
from dfastrbk.src.config import Config

#import contextily as ctx
#from xyzservices import TileProvider

FIGSIZE: tuple[float, float] = (5.748, 5.748)  # Deltares report width
TEXTFONT = 'arial'
TEXTSIZE = 12
CRS: str = 'EPSG:28992' # Netherlands
XMAJORTICK: float = 1000
XMINORTICK: float = 100

def initialize_figure(figsize: Optional[tuple[float, float]] = FIGSIZE) -> Figure:
    font = {'family': TEXTFONT, 'size': TEXTSIZE}
    plt.rc('font', **font)
    fig = plt.figure(figsize=figsize, layout='constrained')
    return fig

def initialize_subplot(fig: Figure, nrows: int, ncols: int, index: int, xlabel: str, ylabel: str):
    ax = fig.add_subplot(nrows,ncols,index)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return ax

def difference_plot(ax: Axes, ylabel: str, color: str):
    secax_y2 = ax.twinx()
    secax_y2.set_ylabel(ylabel)
    secax_y2.yaxis.label.set_color(color)
    secax_y2.tick_params(color=color, labelcolor=color)
    secax_y2.spines['right'].set_color(color)
    return secax_y2

def invert_xaxis(ax: Axes):
    ax.xaxis.set_inverted(True)

def plot_variable(ax: Axes, x: np.ndarray, y: np.ndarray, color: str = 'black') -> Axes:
    p = ax.plot(x, y, '-', linewidth=0.5, color=color)
    return p

# def add_satellite_image(ax: Axes, background_image: TileProvider):
#     ctx.add_basemap(ax=ax, source=background_image, crs=CRS, attribution=False, zorder=-1)

@dataclass
class Plot1DConfig:
    XLABEL: str = 'afstand [rivierkilometer]'
    COLORS = ('k','b','r') # reference, intervention, difference
    LABELS = ['Referentie','Plansituatie']

@dataclass
class Plot2D:
    xlabel: str = 'x-coördinaat [km]'
    ylabel: str = 'y-coördinaat [km]'
    #background_image = ctx.providers.OpenStreetMap.Mapnik #ctx.providers.Esri.WorldImagery

    def initialize_map(self) -> tuple[Figure, Axes]:
        fig = initialize_figure()
        ax = initialize_subplot(fig,1,1,1,self.xlabel,self.ylabel)
        #add_satellite_image(ax, Plot2D.background_image)
        ax.grid(True)
        return fig, ax
    
    def modify_axes(self, ax: Axes):
        ax.set_title('') 
        ax.set_aspect('equal')
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(self.ylabel)
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x/XMAJORTICK:.1f}"))
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x/XMAJORTICK:.1f}"))
        return ax
    
    def plot_profile_line(self, profile: LineString, bedlevel: xr.DataArray, filename: Path):
        """Plot the profile line in a 2D plot"""
        fig, ax = self.initialize_map()
        p = bedlevel.ugrid.plot(ax=ax,add_colorbar=False,cmap='terrain',center=False)
        fig.colorbar(p,ax=ax,label='bodemligging [m]',orientation='horizontal',shrink=0.25)
        shapely.plotting.plot_line(profile, ax=ax, add_points=False, color='black')
        self.modify_axes(ax)
        savefig(fig,filename)
        return fig, ax

def modify_axes(ax: Axes, x_major_tick: float) -> Axes:
    #x-axis:
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x/x_major_tick}"))
    ax.tick_params(which='major',length=8)
    ax.tick_params(which='minor',length=4)
    return ax

def construct_figure_filename(figdir: Path, base: str, extension: str) -> Path:
    """Construct full path for saving a figure."""
    return Path(figdir) / f"{base}{extension}"

@dataclass
class FlowfieldConfig:
    VELOCITY_YLABEL: str = 'stroomsnelheid\nmagnitude' + r' [$m/s$]'
    VELOCITY_DIFF_YLABEL: str = 'verschil plansituatie\n-referentie' + r' [$m/s$]'
    VELOCITY_YMIN: float = 0.0
    ANGLE_YTICKS = ticker.FixedLocator(list(range(-180, 181, 45)))
    ANGLE_PRIMARY_YLABEL: str = 'stromingshoek t.o.v.\nprofiellijn [graden]'
    #ANGLE_SECONDARY_YLABEL: str = r'stromingshoek [richting]'
    ANGLE_DIFF_YLABEL: str = 'verschil plansituatie\n-referentie' + r' [$graden$]'
    #ANGLE_SECONDARY_YTICKLABELS = ticker.FixedFormatter(['Z','ZW','W','NW','N','NO','O','ZO','Z'])
    
@dataclass
class FroudeConfig:
    legend_title = 'Froude getal'

    class Abs:
        colorbar_label: str = 'Froude getal'
        levels: tuple = (0,0.08,0.1,0.15)
        colormap: str = 'RdBu'
    
    class Diff:
        bins: list = [0, 0.08, 0.1, 0.15, np.inf]
        
        # the following variables are linked to the classes returned by _compute_change_classes
        #colors: tuple = ("#d1ffbf", '#49e801', '#267500', '#f80000', '#fea703', '#fffe00')
        colors = ('blue','red')
        labels: list[str] = [#f"van < {bins[3]} naar >= {bins[3]}",
                             #f"van < {bins[2]} naar >= {bins[2]}",
                             f"van < {bins[1]} naar >= {bins[1]}",
                             f"van > {bins[1]} naar <= {bins[1]}"
                             #f"van > {bins[2]} naar <= {bins[2]}",
                             #f"van > {bins[3]} naar <= {bins[3]}"
                             ]
class Ice2D:
    
    def create_map(self, 
                   data: DataArray, 
                   riverkm: LineString,
                   filename: Path) -> None:
        fig, ax = Plot2D().initialize_map()
        p = data.ugrid.plot(ax=ax, 
                            add_colorbar=False, 
                            levels=FroudeConfig.Abs.levels,
                            cmap=FroudeConfig.Abs.colormap)
        fig.colorbar(p,ax=ax,label=FroudeConfig.Abs.colorbar_label,orientation='horizontal',shrink=0.25)
        ax = Plot2D().modify_axes(ax)
        chainage_markers(np.array(riverkm.coords), ax, scale=1)
        savefig(fig,filename)
    
    def create_diff_map(self, 
                        ref_data: xr.DataArray, 
                        variant_data: xr.DataArray, 
                        riverkm: LineString,
                        filename: Path) -> None:
        plt.close('all')
        bins = FroudeConfig.Diff.bins
        colors = FroudeConfig.Diff.colors
        labels = FroudeConfig.Diff.labels

        # Step 1: Digitize inputs
        ref_data_digitized = self._digitize(ref_data.values, bins) 
        variant_data_digitized = self._digitize(variant_data.values, bins) 

        # Step 2: Classify change categories
        classes = self._compute_change_classes(ref_data_digitized, variant_data_digitized)
        variant_data.values = classes

        # Step 3: Initialize figure with background plot
        fig, ax = Plot2D().initialize_map()
        color = "lightgrey"
        ref_masked = ref_data[ref_data_digitized==0]
        ref_masked.ugrid.plot(ax=ax,
                                  cmap=ListedColormap([color]),
                                  add_colorbar=False,
                                  vmin=bins[0],
                                  vmax=bins[1])

        # Step 4: Difference plot
        ax, legend_elements = self._plot_diff_map(ax, variant_data, labels, colors)
        
        # Step 5: finalisation
        ax = Plot2D().modify_axes(ax)
        lgd = fig.legend([Patch(facecolor=color), *legend_elements], 
                   [f"< {bins[1]} in referentie",*labels])
        lgd.set_title(FroudeConfig.legend_title)
        ax.grid(True)
        chainage_markers(np.array(riverkm.coords), ax, scale=1)
        savefig(fig,filename)

    def _plot_diff_map(self, 
                       ax: Axes, 
                       diff_data: xr.DataArray, 
                       labels: list[str],
                       colors: tuple) -> tuple[Axes, list]:
        
        xu.plot.pcolormesh(diff_data.grid,diff_data,ax=ax,
            add_colorbar=False,
            cmap=ListedColormap(colors),
            zorder=1)
        
        legend_elements = [
            Patch(facecolor=colors[i], label=labels[i])
            for i in range(len(labels))
        ]

        return ax, legend_elements
    
    def _digitize(self, data: Any, bins: Any) -> np.ndarray:
        return np.digitize(data, bins) - 1
    
    def _compute_change_classes(self, 
                                ref_data: np.ndarray, 
                                variant_data: np.ndarray) -> np.ndarray:
        """Computes how classes change between two digitized datasets"""
        classes = variant_data * np.nan

        conditions = [#(ref_data < 3) & (variant_data >= 3),
            #(ref_data < 2) & (variant_data >= 2),
            (ref_data < 1) & (variant_data >= 1),
            (ref_data > 0) & (variant_data <= 0)
            #(ref_data > 1) & (variant_data <= 1),
            #(ref_data > 2) & (variant_data <= 2)
        ]

        for i, cond in enumerate(conditions, start=1):
            classes[cond] = i

        return classes

class Ice1D:
    """Class for plotting 1D river flow velocity and angle."""
    
    def plot_velocity_magnitude(self, 
                                ax: Axes,
                                 distance: np.ndarray, 
                                 velocity: np.ndarray, 
                                 color: str) -> Axes:
        """
        Plot the velocity magnitude.
        """
        plot_variable(ax, distance, velocity, color)
        ax.set_ylim(bottom=FlowfieldConfig.VELOCITY_YMIN)
        return ax

    def plot_velocity_angle(self, 
                            ax: Axes, 
                            distance: np.ndarray, 
                            angle: np.ndarray,
                            color: str) -> Axes:
        """
        Plot the velocity angle in a separate subplot.
        """
        plot_variable(ax, distance, angle, color)
        return ax

    # def angle_direction(self, ax: Axes):
    #     secax_y = ax.secondary_yaxis(-0.2)
    #     for ax in [ax,secax_y]:
    #     secax_y.yaxis.set_major_formatter(FlowfieldConfig.ANGLE_SECONDARY_YTICKLABELS)
    #     secax_y.set_ylabel(FlowfieldConfig.ANGLE_SECONDARY_YLABEL)
    #     return secax_y
    
    def create_figure(self,
                      distance: np.ndarray, 
                      velocity: list, 
                      angle: list,
                      configuration: Config,
                      filename: Path) -> None:
        """
        Create and display a figure with velocity magnitude and angle.
        """
        plt.close('all')
        fig = initialize_figure()
        config = Plot1DConfig()
        
        ax1 = initialize_subplot(fig,2,1,1,config.XLABEL,FlowfieldConfig.VELOCITY_YLABEL)
        ax2 = initialize_subplot(fig,2,1,2,config.XLABEL,FlowfieldConfig.ANGLE_PRIMARY_YLABEL)

        for i, (v, a) in enumerate(zip(velocity,angle)):
            ax1 = self.plot_velocity_magnitude(ax1, distance, v, Plot1DConfig.COLORS[i])
            ax2 = self.plot_velocity_angle(ax2, distance, a, Plot1DConfig.COLORS[i])
        
        if len(velocity)>1:
            ax3 = difference_plot(ax1,FlowfieldConfig.VELOCITY_DIFF_YLABEL,Plot1DConfig.COLORS[-1])
            ax4 = difference_plot(ax2,FlowfieldConfig.ANGLE_DIFF_YLABEL,Plot1DConfig.COLORS[-1])
            ax3 = self.plot_velocity_magnitude(ax3,distance,velocity[1]-velocity[0],Plot1DConfig.COLORS[-1])
            ax4 = self.plot_velocity_angle(ax4,distance,angle[1]-angle[0],Plot1DConfig.COLORS[-1])
        
        for ax in [ax1,ax2]:
            ax1 = modify_axes(ax1,XMAJORTICK)
            ax2 = modify_axes(ax2,XMAJORTICK)
            if configuration.general.bool_flags['invertxaxis']:
                invert_xaxis(ax)
        ax2.yaxis.set_major_locator(FlowfieldConfig.ANGLE_YTICKS)
        ax2.set_ylim(-180, 180)

        ax1.legend(Plot1DConfig.LABELS, bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
                      ncols=2, borderaxespad=0.)
        savefig(fig,filename)

@dataclass
class CrossFlowConfig:
    XLABEL = Plot1DConfig.XLABEL
    YLABEL: str = r'dwarsstroomsnelheid [$m/s$]'
    DIFF_YLABEL: str = 'verschil in dwars-\nstroomsnelheid' + r' [$m/s$]'
    CRITERIA: tuple[float, float] = (0.15, 0.3)  # criteria for transverse velocity

class CrossFlow:
    def __init__(self, config: CrossFlowConfig = CrossFlowConfig()):
        self.config = config

    def prepare_data(self, distance: np.ndarray, transverse_velocity: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Prepare data by inserting array roots and subsequently splitting into blocks."""
        distance_app, transverse_velocity_app = operations.insert_array_roots(distance, transverse_velocity)
        distance_split, transverse_velocity_split = operations.split_into_blocks(distance_app, transverse_velocity_app)
        return distance_split, transverse_velocity_split
    
    def plot_discharge(
        self,
        ax: Axes,
        distance_split: np.ndarray,
        transverse_velocity_split: np.ndarray,
        ship_depth: float,
        ship_length: float,
        criteria: tuple[float, float]
    ) -> Optional[Line2D]:
        """
        Calculate and plot perpendicular discharge according to RBK specifications,
        along with the discharge criteria line.

        Returns:
            A matplotlib Line2D object representing the criteria line, or None if no data was plotted.
        """
        crit_handle = None

        for xi, yi in zip(distance_split, transverse_velocity_split):
            if not np.any(yi):
                continue

            max_integral, indices = operations.max_rolling_integral(xi, yi, ship_length)
            discharge = flow.trans_discharge(max_integral, ship_depth)

            start_idx, end_idx = indices[0], indices[-1] + 1
            xi_segment = xi[start_idx:end_idx]
            yi_segment = yi[start_idx:end_idx]

            ax.fill_between(xi_segment, yi_segment, color='lightgrey', interpolate=True)
            ax.axvline(xi[start_idx], color='black', lw=0.5, ls='--')
            ax.axvline(xi[end_idx - 1], color='black', lw=0.5, ls='--')

            crit_value = criteria[1] if discharge < 50.0 else criteria[0]
            if np.any(yi < 0):
                crit_value = -crit_value
            crit_handle = ax.hlines(crit_value, xi[start_idx], xi[end_idx - 1], color='red', lw=1, ls='-')

        return crit_handle

    #TODO: save fig
    def create_figure(self, 
                      distance: np.ndarray, 
                      transverse_velocity: list, 
                      ship_depth: float,
                      ship_length: float,
                      inverse_xaxis: bool,
                      filename: Path) -> None:
        plt.close('all')
        fig = initialize_figure()
        axs=[]
        ax1 = initialize_subplot(fig,len(transverse_velocity),1,1,self.config.XLABEL,self.config.YLABEL)
        axs.append(ax1)

        lines=[]
        for i, v in enumerate(transverse_velocity):
            line, = plot_variable(ax1, distance, v, Plot1DConfig.COLORS[i])
            lines.append(line)

            if i == len(transverse_velocity) - 1: # only prepare data for plot_discharge at the last iteration
                distance_split, transverse_velocity_split = self.prepare_data(distance, v) 

        if len(transverse_velocity)>1:
            ax2 = initialize_subplot(fig,2,1,2,self.config.XLABEL, CrossFlowConfig.DIFF_YLABEL)
            plot_variable(ax2, distance, transverse_velocity[1] - transverse_velocity[0])
            yabs_max = abs(max(ax2.get_ylim(), key=abs))
            ax2.set_ylim(ymin=-yabs_max, ymax=yabs_max)
            axs.append(ax2)

        crit_handle = self.plot_discharge(ax1, 
                                    distance_split, 
                                    transverse_velocity_split, 
                                    ship_depth, 
                                    ship_length, 
                                    self.config.CRITERIA)
        for ax in axs:
            modify_axes(ax, XMAJORTICK)
            ax.axhline(0,color='black',ls='--')
            if inverse_xaxis: 
                invert_xaxis(ax)
        
        # Combine lines and crit_handle, filtering out None
        handles = [*lines]
        labels = [*Plot1DConfig.LABELS[0:len(transverse_velocity)]]

        if crit_handle is not None:
            handles.append(crit_handle)
            labels.append('criteria')

        ax1.legend(
            handles,
            labels,
            bbox_to_anchor=(0., 1.02, 1., .102),
            loc='lower left',
            ncols=3,
            borderaxespad=0.
        )

        savefig(fig,filename)
