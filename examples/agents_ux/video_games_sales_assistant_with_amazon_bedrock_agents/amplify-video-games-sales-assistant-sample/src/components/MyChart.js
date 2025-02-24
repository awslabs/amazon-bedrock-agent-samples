import React from "react";
import Chart from "react-apexcharts";

function MyChart(props) {
    const { options, series, type } = props;    
    return (
      <div>
            <div id="chart">
                  <Chart options={options} series={series} type={type} height={420} />
            </div>
      </div>
    );
}

export default MyChart;