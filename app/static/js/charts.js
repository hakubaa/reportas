function BarChart(config) {
    this.ctx = config.ctx;
    this.timerange = config.timerange;
    this.config = {
        type: "bar",
        data: {
            labels: [],
            datasets: []
        },
        options: this.getDefaultOptions()
    };
    this.chart = this.createChart();
}

BarChart.prototype.createChart = function(metadata) {
    var chart = new Chart(this.ctx, this.config);
    return chart;
}

BarChart.prototype.getDefaultOptions = function() {
    return {
        scales: {
            yAxes: [{
                ticks: {
                    beginAtZero:true
                }
            }],
            xAxes: [{
                ticks: {
                    callback: function(value, index, values) {
                        return formatTimestamp(value);
                    }
                }
            }]
        }
    };
}

BarChart.prototype.extractLabels = function(data) {
    var labels = data.map(function(item) { return item.timestamp; });
    return labels;
}

BarChart.prototype.extractData = function(data) {
    var data = data.sort(function(x, y) {
            return moment(x.timestamp) - moment(y.timestamp);
        })
        .map(function(item) { 
            return {
                "y": item.value,
                "x": item.timestamp
            }
        });
    return data;    
}

BarChart.prototype.appendDataset = function(data, label) {
    this.labels = this.labels.concat(this.extractLabels(data));

    var data = this.extractData(data);
    this.appendMissingDataPoints(data, this.labels);
    data = this.sortDataPoints(data);

    this.datasets.push(this.createDataset({data: data,label: label}));
    
    this.adjustLabels();
    this.adjustDatasets();
    this.chart.update();
}

BarChart.prototype.appendMissingDataPoints = function(data, labels) {
    var dp_labels = data.map(function(item) { return item.x; });
    for(var i = 0; i < labels.length; i++) {
        if (dp_labels.indexOf(labels[i]) < 0) {
            data.push({"y": null, "x": this.labels[i]});
        }
    }
}

BarChart.prototype.sortDataPoints = function(data) {
    return data.sort(function(x, y) { return moment(x.x) - moment(y.x) });
}


BarChart.prototype.createDataset = function(config) {
    var options = {
        borderColor: "black",
        borderWidth: 1,
        backgroundColor: this.createBackgroundColors(config.data)
    };
    $.extend(options, config)
    return options;
}

BarChart.prototype.createBackgroundColors = function(data) {
    return data.map(function(d) {
        if (d.y > 0) {
            return "limegreen";
        } else {
            return "red";
        }
    });
}

BarChart.prototype.adjustLabels = function() {
    var labels = distinct(this.labels);
    labels = labels.concat(this.createMissingLabels(labels));
    this.labels = labels.sort(function(x, y) { 
        return moment(x) - moment(y); 
    });
}

BarChart.prototype.createMissingLabels = function(labels) {
    return [];
}

BarChart.prototype.adjustDatasets = function() {
    for(var i = 0; i < this.datasets.length; i++) {
        var data = this.datasets[i].data;
        this.appendMissingDataPoints(data, this.labels);
        data = this.sortDataPoints(data);
        this.datasets[i].data = data;
        this.datasets[i].backgroundColor = this.createBackgroundColors(data);
    }
}

Object.defineProperty(BarChart.prototype, "labels", {
    get: function() { 
        return this.config.data.labels;
    },
    set: function(labels) {
        this.config.data.labels = labels;
    }
});

Object.defineProperty(BarChart.prototype, "datasets", {
    get: function() { 
        return this.config.data.datasets;
    },
    set: function(value) {
        this.config.data.datasets = datasets;
    }
});