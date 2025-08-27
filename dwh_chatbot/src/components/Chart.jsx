import React from 'react';
import Plot from 'react-plotly.js';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Bar, Pie, Doughnut, Scatter } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const Chart = ({ plotlyJson, chartData, bare = false }) => {
  // Handle both plotlyJson (legacy) and chartData (new backend)
  const data = plotlyJson || chartData;
  
  if (!data) {
    return (
      <div className="w-full min-h-[400px] flex items-center justify-center text-gray-500">
        No chart data available
      </div>
    );
  }

  // Check if it's Chart.js format (new backend)
  if (data.type && data.data && data.options) {
    const chartComponent = () => {
      const chartProps = {
        data: data.data,
        options: {
          ...data.options,
          responsive: true,
          maintainAspectRatio: false,
        }
      };

      switch (data.type.toLowerCase()) {
        case 'line':
          return <Line {...chartProps} />;
        case 'bar':
          return <Bar {...chartProps} />;
        case 'pie':
          return <Pie {...chartProps} />;
        case 'doughnut':
          return <Doughnut {...chartProps} />;
        case 'scatter':
          return <Scatter {...chartProps} />;
        default:
          return <Bar {...chartProps} />; // Default to bar chart
      }
    };

    const chartElement = (
      <div className="w-full h-[400px] flex items-center justify-center">
        {chartComponent()}
      </div>
    );

    if (bare) {
      return chartElement;
    }

    return (
      <div className="mt-6 p-4 bg-white rounded-xl border border-gray-100 shadow-md hover:shadow-lg transition-all duration-300">
        {chartElement}
      </div>
    );
  }

  // Check if it's Plotly format (legacy or converted)
  if (data.data && data.layout) {
    const plotComponent = (
      <Plot
        data={data.data}
        layout={{
          ...data.layout,
          autosize: true,
          responsive: true,
        }}
        config={{
          ...data.config,
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        }}
        useResizeHandler={true}
        style={{ width: '100%', height: '400px' }}
      />
    );

    if (bare) {
      return <div className="w-full min-h-[400px]">{plotComponent}</div>;
    }

    return (
      <div className="mt-6 p-4 bg-white rounded-xl border border-gray-100 shadow-md hover:shadow-lg transition-all duration-300">
        <div className="w-full min-h-[400px]">{plotComponent}</div>
      </div>
    );
  }

  // Fallback for unknown data format
  return (
    <div className="w-full min-h-[400px] flex items-center justify-center text-gray-500">
      <div className="text-center">
        <div className="text-lg font-medium mb-2">Chart Data Received</div>
        <div className="text-sm text-gray-400 mb-4">
          Data format: {typeof data === 'object' ? 'Object' : typeof data}
        </div>
        <div className="bg-gray-100 p-3 rounded text-xs text-gray-600 max-h-32 overflow-y-auto">
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      </div>
    </div>
  );
};

export default Chart;