from highcharts_core.chart import Chart
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.bar import ColumnSeries
from matplotlib.cbook import boxplot_stats
import pandas as pd
import numpy as np


class Highcharts:

    def __init__(self, input_df, unit=None):

        colors = ['#f8902d', '#8b6ea6', '#6ebe43', '#9c7848', '#e0592a', '#c28942', '#41796c']

        self.df = input_df
        self.unit = unit
        self.color = colors

    def boxplot(self):
        df_boxplot_stats = pd.DataFrame({'whislo': [], 'q1': [], 'med': [], 'q3': [], 'whishi': []})
        df_boxplot_outliers = pd.DataFrame({'parameter': [], 'value': []})

        for i in list(self.df.columns):
            boxplot = boxplot_stats(self.df[i].dropna())
            boxplot = pd.DataFrame(boxplot)
            boxplot = boxplot.drop(['mean', 'iqr', 'cilo', 'cihi', 'fliers'], axis=1)
            whishi = boxplot.pop('whishi')
            boxplot.insert(4, 'whishi', whishi)
            df_boxplot_stats = pd.concat([df_boxplot_stats, boxplot])
            outliers = self.df[i][(self.df[i] < boxplot['whislo'].values[0]) | (self.df[i] > boxplot['whishi'].values[0])]
            df_boxplot_outliers = pd.concat(
                [df_boxplot_outliers, pd.DataFrame({'parameter': i, 'value': outliers.values})])

        df_boxplot_stats = df_boxplot_stats.transpose().set_axis(list(self.df.columns.values), axis=1)

        columns = list(df_boxplot_stats.columns)
        data = list(df_boxplot_stats[x].values.tolist() for x in columns)

        index_list = []
        outliers_list = []
        for i in df_boxplot_outliers['parameter'].values.tolist():
            index_list.append(columns.index(i))
        df_boxplot_outliers['index'] = index_list

        for i in range(len(df_boxplot_outliers)):
            outliers_list.append(
                [df_boxplot_outliers['index'].values.tolist()[i], df_boxplot_outliers['value'].values.tolist()[i]])

        data = [{
            "name": "Boxplot",
            "data": data,
            "tooltip": {
                "headerFormat": '<em>Parameter {point.key}</em><br/>'
            },
            "type": 'boxplot', 'color':self.color[0]}, {
            "name": "Extreme value",
            "data": outliers_list,
            "type": 'scatter',
            "marker": {
                "fillColor": 'white',
                "lineWidth": 0.5,
                "lineColor": self.color[0]
            },
            "tooltip": {
                "headerFormat": '<em>Parameter {point.key}</em><br/>',
                "pointFormat": '<b>Extreme value</b> <br/> Concentration: {point.y} ' f'{self.unit}'
            }}
        ]

        options_kwargs = {
            'title': {
                'text': 'Boxplot per Parameter'
            },

            'legend': {
                'enabled': False
            },

            'xAxis': {
                'categories': columns,
                'title': {
                    'text': 'Parameter'
                }
            },

            'yAxis': {
                'type': 'logarithmic',
                'minorTickInterval': 0.1,
                'title': {
                    'text': f'Concentration (log {self.unit})'
                }
            }
        }
        chart = Chart(options=options_kwargs, container='boxplot')
        chart.add_series(*data)

        as_js_literal = chart.to_js_literal('./interactive_plots/rendering/boxplot.js')

        return as_js_literal

    def correlation_heatmap(self, container, data_info, max_df=None, count=None):

        data_highcharts = []

        columns = list(self.df.columns)
        data = list(self.df[x].values.tolist() for x in columns)
        count_data = list(count[x].values.tolist() for x in columns)
        names = []
        count = []

        for i in range(len(data)):
            for j in range(len(data)):
                names.append(f'{columns[i]}-{columns[j]}')
                data_highcharts.append({'x': i, 'y': j, 'value': data[i][j], 'name': f'{int(count_data[i][j])}'})
                count.append(count_data[i][j])

        data = [{
            "name": "Correlation",
            "borderWidth": 1,
            "data": data_highcharts,
            "type": 'heatmap',
            "dataLabels": [{"enabled": True,
                            'format': '{point.value:,.2f} <br> ({point.options.name})'}]
        }
        ]

        max = max_df if max_df else 1

        options_kwargs = {
            'title': {
                'text': f'Correlation {data_info}'
            },
            'legend': {
                'align': 'right',
                'layout': 'vertical',
                'margin': 0,
                'verticalAlign': 'top',
                'y': 25,
                'symbolHeight': 280,
            },
            'xAxis': {
                'categories': columns,
                'title': {
                    'text': 'Parameter'
                }
            },
            'yAxis': {
                'categories': columns,
                'title': {
                    'text': f'Parameter'
                },
                'reversed': True
            },
            'colorAxis': {
                'reversed': False,
                'min': 0,
                'max': max,
                'minColor': '#FFFFFF',
                'maxColor': self.color[0],
            },
            'chart': {
                'type': 'heatmap',
                'marginTop': 40,
                'marginBottom': 80,
            },
            'tooltip': {
                'formatter': 'function() {return this.series.xAxis.categories[this.point.x] + " - " + this.series.yAxis.categories[this.point.y] + "<br> Correlation : " + Highcharts.numberFormat(this.point.value,2) + "<br> Count : " + this.point.options.name}'
            },
        }

        chart = Chart(options=options_kwargs, container=container)
        chart.add_series(*data)

        as_js_literal = chart.to_js_literal(f'./interactive_plots/rendering/{container}.js')

        return as_js_literal

    def correlation_scatterplot_matrix(self):

        data_highcharts = []
        columns = list(self.df.columns)

        for i in range(len(columns)):
            for k in range(len(columns)):
                scatter_data = []
                for j in range(len(self.df)):
                    scatter_data.append([self.df[columns[i]][j].round(2), self.df[columns[k]][j].round(2)])

                data_highcharts.append(
                    {"name": f'{columns[i]}-{columns[k]}', "data": scatter_data, "type": 'scatter', 'xAxis': i,
                     'yAxis': k, "color": '#f8902d', 'marker': {'symbol': 'circle'}})

        count = int(len(columns)) + 1

        yAxis = [{
            'min': 0,
            'tickAmount':3,
            'allowDecimals': False,
            'title': {
                'text': f'{columns[0]}'
            },
            'height': f'{int(100 / count)}%',
        }]
        xAxis = [{
            'min': 0,
            'allowDecimals': False,
            'title': {
                'text': f'{columns[0]}'
            },
            'width': f'{int(100 / count)}%',
        }]

        for i in range(1, count - 1):
            yAxis.append({
            'min': 0,
            'tickAmount':3,
            'allowDecimals':False,
                'title': {
                    'text': f'{columns[i]}'
                },
                'top': f'{((i * int(100 / count)) + i * (int(100 / count) / (count - 2)))}%',
                'height': f'{int(100 / count)}%',
                'offset': 0,
            })

            xAxis.append({
            'allowDecimals':False,
            'min': 0,
                'title': {
                    'text': f'{columns[i]}'
                },
                'left': f'{(i * int(100 / count) + i * int(100 / count) / (count - 2))}%',
                'width': f'{int(100 / count)}%',
                'offset': 0,
            })

        options_kwargs = {

            'title': {
                'text': 'Scatterplot of parameters'
            },

            'legend': {
                'enabled': False
            },

            'yAxis': yAxis,

            'xAxis': xAxis,

            "tooltip": {
                "pointFormat": '{point.series.name} <br/> {point.x:,.2f}-{point.y:,.2f}'
            },
            'plotOptions': {
                'scatter': {
                    'marker': {
                        'radius': 10/len(columns),
                        'symbol': 'circle'}}}

        }

        chart = Chart(options=options_kwargs, container='correlation_scatterplot_matrix')
        chart.add_series(*data_highcharts)

        as_js_literal = chart.to_js_literal('./interactive_plots/rendering/correlation_scatterplot_matrix.js')

        return as_js_literal

    def count_datapoints_timeseries(self):

        series = [LineSeries.from_pandas(self.df, property_map={'y': 'count', 'x': 'date'}, series_kwargs={'name': 'VMM groundwater', 'color':self.color[0]})]

        options_kwargs = {
            'chart': {
                'zooming': {
                    'key': 'shift',
                    'type': 'x'
                },
              },
            'title': {
                'text': 'Count of datapoints'
            },

            'legend': {
                'enabled': True
            },

            'xAxis': {
                'type': 'datetime',
                'title': {
                    'text': 'Date'
                }
            },

            'yAxis': {
                'title': {
                    'text': 'Count'
                }
            }
        }

        chart = Chart(options=options_kwargs, container='count_datapoints_timeseries')
        chart.add_series(*series)

        as_js_literal = chart.to_js_literal('./interactive_plots/rendering/count_datapoints_timeseries.js')

        return as_js_literal

    def histogram(self):

        series = [{
            'name': 'Histogram',
            'type': 'histogram',
            'xAxis': 1,
            'yAxis': 1,
            'baseSeries': 's1'
        }, {
            'name': 'Data',
            'data': self.df,
            'type': 'scatter',
            'id': 's1',
            'visible': False
        }]

        options_kwargs = {

            'title': {
                'text': 'Distance histogram'
            },

            'legend': {
                'enabled': False
            },

            'xAxis': [{
                'title': {'text': ''},
                'alignTicks': False
            }, {
                'title': {'text': ''},
                'alignTicks': False,
            }],

            'yAxis': [{
                'title': {'text': ''}
            }, {
                'title': {'text': 'Histogram'},
            }],
            'plotOptions': {
                'histogram': {
                    'accessibility': {
                        'point': {
                            'valueDescriptionFormat': '{index}. {point.x:.3f} to {point.x2:.3f}, {point.y}.'
                        }
                    }
                }
            }
        }

        chart = Chart(options=options_kwargs, container='histogram')
        chart.add_series(*series)

        as_js_literal = chart.to_js_literal('./interactive_plots/rendering/histogram.js')

        return as_js_literal

    def column_plot(self):

        series = [ColumnSeries.from_pandas(self.df, property_map = {'y': 'count', 'x': 'bin_mean', 'id': 'bin_edges'}, series_kwargs={'name': 'VMM groundwater', 'color':self.color[0]})]

        options_kwargs = {
            'chart': {
                'zooming': {
                    'key': 'shift',
                    'type': 'x'
                },
            },
            'title': {
                'text': 'Distance histogram'
            },

            'legend': {
                'enabled': True
            },

            'xAxis': {
                'title': {
                    'text': 'Distance (m)'
                }
            },

            'yAxis': {
                'title': {
                    'text': 'Count'
                }
            },
            "tooltip": {
                "pointFormat": 'Distance interval: {point.id}<br/> Count: {point.y}'
            },
            "plotOptions": {'column' : {'groupPadding': 0,
                'pointPadding': 0}
        }}

        chart = Chart(options=options_kwargs, container='distance_histogram')
        chart.add_series(*series)

        as_js_literal = chart.to_js_literal('./interactive_plots/rendering/distance_histogram.js')

        return as_js_literal



if __name__ == '__main__':

    input_df = pd.read_csv('from-pandas.csv')
    highcharts = Highcharts(input_df)

    highcharts.boxplot()
