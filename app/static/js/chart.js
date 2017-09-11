/*------------------------------------------------------------------------------
  Chart
------------------------------------------------------------------------------*/

function Chart(config) {
    if (config === undefined) config = {};
    this.svg = d3.select(config.svg);
    this.series = {};
    this.config = { // default configs
        "left-scale": d3.scaleLinear,
        "left-scale-reverse": true,
        "right-scale": d3.scaleLinear,
        "x-scale": d3.scaleLinear,
        "margin": { left: 50, top: 50, right: 50, bottom: 25 }
    }
    $.extend(this.config, config);
}

Chart.prototype.appendSeries = function(config) {
    if (config === undefined) config = {};
    if (config.axis === undefined) config.axis = "left";

    var key = config.key;
    if (key === undefined) {
        var indexes = Object.keys(this.series);
        if (indexes.length > 0) {
            key = Math.max(indexes) + 1; 
        } else {
            key = 0;
        }
    }
    this.series[key] = {
        data: config.data,
        axis: config.axis
    };
    return key;
}

Chart.prototype.getSeries = function(key) {
    return this.series[key].data;
}

Chart.prototype.update = function() {
    var margin = this.config.margin;
    var g = this.svg.append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var xScale = this.getXScale();
    var yScale = this.getLeftScale();

    g.selectAll("circle")
        .data(this.series["0"].data, function(d) { return d.id; })
        .enter().append("circle")
        .attr("r", 5)
        .attr("cx", function(d, i) { return xScale(d.x); })
        .attr("cy", function(d, i) { return yScale(d.y); })
        .style("fill", "grey");

    var xAxis = d3.axisBottom().scale(xScale).tickSize(this.height).ticks(d3.timeYear);
    g.append("g").attr("id", "xAxisG").call(xAxis);

    var rightAxis = d3.axisRight().scale(yScale).tickSize(this.width).ticks(10);
    g.append("g").attr("id", "valueAxisG").call(rightAxis);


        // .append("g")
        // .selectAll("g")
        // .data(data.series["0"].data)
        // .enter().append("g")
        //     .attr("transform", function(d) { 
        //         return "translate(" + yScale(d.y) + ",0)"; 
        //     })
    var height = this.height;
    g.selectAll("rect")
        .data(this.series["0"].data)
        .enter().append("rect")
            .attr("x", function(d) { return xScale(d.x); })
            .attr("y", function(d) { return yScale(d.y); })
            .attr("width", 10)
            .attr("height", function(d) { return height - yScale(d.y); })
            .attr("fill", "red");


    var bars = svg.selectAll("g.record")
        .data(data).enter().append("g")
        .attr("class", "record")
        .attr("transform", function(d, i) {
            var dx = xScale(d.y);
            var dy = d.x > 0 ? valueScale(d.x) : valueScale(0);
            return "translate(" + dx + ", " + dy + ")";
        });

    bars.append("rect")
        .attr("width", barWidth)
        .attr("height", function(d, i) {
            if (d.value > 0) { 
                return valueScale(heightBase) - valueScale(d.value); 
            } else {
                return valueScale(d.value) - valueScale(heightBase);
            }
        })    
        .style("fill", function(d, i) {
            if (d.value > 0) {
                return "limegreen";
            } else {
                return "red";
            }
        })
        .style("opacity", 0.75)
        .attr("stroke", "black")
        .attr("stroke-width", 1);

}

Chart.prototype.getLeftScale = function() {
    var values = this.getValues(
        Object.values(this.series).filter(function(series) {
            return series.axis == "left";
        }), "y"
    );
    var extent = d3.extent(values);
    var scale = this.config["left-scale"]().domain(extent);
    if (this.config["left-scale-reverse"]) {
        scale.range([this.height, 0]);
    } else {
        scale.range([0, this.height]);
    }
    return scale;
}

Chart.prototype.getRightScale = function() {
    var values = this.getValues(
        Object.values(this.series).filter(function(series) {
            return series.axis == "right";
        }), "y"
    );
    var extent = d3.extent(values);
    return this.config["right-scale"]().domain(extent).range([0, this.height]);
}

Chart.prototype.getXScale = function() {
    var values = this.getValues(Object.values(this.series), "x");
    var extent = d3.extent(values);
    return this.config["x-scale"]().domain(extent).range([0, this.width]);
}

Chart.prototype.getValues = function(series, key) {
    var values = Object.values(series)
        .map(function(sr) {
            return sr.data.map(function(item) { return item[key]; });
        })
        .reduce(function(x, y) {
            return x.concat(y); 
        }, []);   
    return values; 
}

Chart.prototype.getBoundingClientRect = function() {
    if (this.svg.size() === 0) {
        return {
            "width": -1, "height": -1, 
            "x": -1, "y": -1
        };
    }
    return this.svg.node().getBoundingClientRect();
}

/*------------------------------------------------------------------------------
  Getters
------------------------------------------------------------------------------*/

Object.defineProperty(Chart.prototype, "width", {
    get: function() { 
        var clientRect = this.getBoundingClientRect();
        var margin = this.config.margin;
        return clientRect.width - margin.left - margin.right;
    }
});

Object.defineProperty(Chart.prototype, "height", {
    get: function() { 
        var clientRect = this.getBoundingClientRect();
        var margin = this.config.margin;
        return clientRect.height - margin.top - margin.bottom;
    }
});

/*----------------------------------------------------------------------------*/