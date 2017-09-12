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
        "margin": { left: 100, top: 20, right: 20, bottom: 20 }
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

function formatTimestamp(timestamp, format) {
    if (format === undefined) format = "YYYY-MM";
    return timestamp.format(format);
}

Chart.prototype.update = function() {
    var margin = this.config.margin;
    var g = this.svg.append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var values = this.getValues(Object.values(this.series), "x")
        .sort().reverse().map(function(x) { return formatTimestamp(x); });
    var xScale = d3.scaleBand().domain(values).range([0, this.width])
        .round(0.1).paddingInner(0.05).round(true);

    var yScale = this.getLeftScale();

    var xAxis = d3.axisBottom().scale(xScale)
        .tickPadding(5);
    
    var rightAxis = d3.axisLeft().scale(yScale)
        .tickSize(this.width).ticks(10).tickSize(10)
        .tickPadding(5);

    g.append("g")
        .attr("id", "xAxisG")
        .attr("transform", "translate(0," + this.height + ")")
        .call(xAxis);

    g.append("g")
        .attr("id", "valueAxisG")
        .attr("transform", "translate(0, 0)")
        .call(rightAxis);

    var baseLevel = Math.max(0, yScale.domain()[0]);

    g.selectAll("rect")
        .data(this.series["0"].data)
        .enter().append("rect")
            .attr("x", function(d) { return xScale(formatTimestamp(d.x)); })
            .attr("y", function(d) { return yScale(Math.max(baseLevel, d.y)); })
            .attr("width", xScale.bandwidth())
            .attr("height", function(d) { return Math.abs(yScale(baseLevel) - yScale(d.y)); })
            .attr("fill", function(d) {
                if (d.y < baseLevel) {
                    return "red";
                } else {
                    return "limegreen";
                }
            })
            .attr("opacity", 0.5);
}


Chart.prototype.getLeftScale = function() {
    var values = this.getValues(
        Object.values(this.series).filter(function(series) {
            return series.axis == "left";
        }), "y"
    );
    var maxValue = d3.max(values);
    var minValue = d3.min(values);
    if (minValue > 0) {
        minValue = 0;
    }
    var scale = this.config["left-scale"]().domain([minValue, maxValue]);
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