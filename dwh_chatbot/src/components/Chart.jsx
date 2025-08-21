import React from 'react';
import Plot from 'react-plotly.js';

const Chart = ({ plotlyJson, bare = false }) => {
  if (!plotlyJson || !plotlyJson.data) {
    return (
      <div className="w-full min-h-[400px] flex items-center justify-center text-gray-500">
        No chart data available
      </div>
    );
  }

  const plotComponent = (
    <Plot
      data={plotlyJson.data}
      layout={{
        ...plotlyJson.layout,
        autosize: true,
        responsive: true,
      }}
      config={{
        ...plotlyJson.config,
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
};

export default Chart;