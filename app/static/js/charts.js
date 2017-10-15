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

BarChart.prototype.appendDataset = function(data, label, id) {
    if (this.indexOfDataset(id) >= 0) {
        throw "Dataset ID in use.";
    } else {
        this.updateLabels(this.extractLabels(data));
        var dataset = this.createDataset({
            data: this.extractData(data), 
            label: label, id: id
        });
        this.updateDatasets(dataset);
        this.chart.update();
    }
}

BarChart.prototype.updateLabels = function(labels) {
    if (labels === undefined) labels = [];
    labels = distinct(this.labels.concat(labels));
    labels = labels.concat(this.createMissingLabels(labels));
    this.labels = labels.sort(function(x, y) { 
        return moment(x) - moment(y); 
    });
}

// TODO: create labels for missing timestamps
BarChart.prototype.createMissingLabels = function(labels) {
    return [];
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

BarChart.prototype.updateDatasets = function(dataset) {
    if (dataset !== undefined) {
        this.datasets.push(dataset);
    }
    for(var i = 0; i < this.datasets.length; i++) {
        var data = this.datasets[i].data;
        this.appendMissingDataPoints(data);
        data = this.sortDataPoints(data);
        this.datasets[i].data = data;
        this.datasets[i].backgroundColor = this.createBackgroundColors(data);
    }
}

BarChart.prototype.appendMissingDataPoints = function(data) {
    // Serialise x-ticks (timestamps - dates) to numbers in order to enable 
    // to search them for missing timestamps that have to be add.
    var dp_labels = data.map(function(item) { return item.x; }).map(Number);
    for(var i = 0; i < this.labels.length; i++) {
        if (dp_labels.indexOf(+this.labels[i]) < 0) { // '+' - serialise
            data.push({"y": null, "x": this.labels[i]});
        }
    }
}

BarChart.prototype.sortDataPoints = function(data) {
    return data.sort(function(x, y) { return moment(x.x) - moment(y.x) });
}

BarChart.prototype.update = function() {
    this.removeEmptyMarginalDataPoints();
    this.chart.update();
}

BarChart.prototype.removeEmptyMarginalDataPoints = function() {
    this.removeLeftSideEmptyDataPoints();
    this.removeRightSideEmptyDataPoints();
}

BarChart.prototype.removeLeftSideEmptyDataPoints = function() {
    var emptyDataPoints = this.filterLeftSideDataPoints(
        this.identifyEmptyDataPoints()
    );
    this.removeDataPoints(emptyDataPoints.sort().reverse());
}

BarChart.prototype.filterLeftSideDataPoints = function(indexes) {
    var lefti = [];
    for (var i = 0; i < indexes.length; i++) {
        if (indexes.indexOf(i) < 0) {
            break;
        } 
        lefti.push(i);
    }
    return lefti;
}

BarChart.prototype.identifyEmptyDataPoints = function() {
    var valuesTrace = new Array(this.labels.length).fill(0);
    for (var i = 0; i < this.datasets.length; i++) {
        for (var j = 0; j < this.datasets[i].data.length; j++) {
            if (this.datasets[i].data[j].y !== null) {
                valuesTrace[j] += 1;
            }
        }
    }
    var indexes = Array.apply(null, {length: this.labels.length})
        .map(Number.call, Number) // range (0 to N)
        .filter(function(item, index, array) {
            return valuesTrace[index] === 0;
        });
    return indexes;
}

BarChart.prototype.removeDataPoints = function(indexes) {
    for (var i = 0; i < indexes.length; i++) { // start from the end
        this.removeDataPoint(indexes[i]);
    }
}

BarChart.prototype.removeDataPoint = function(index) {
    this.labels.splice(index, 1);
    this.datasets.forEach(function(dataset, index) {
        dataset.data.splice(0, 1); 
    });
}

BarChart.prototype.removeRightSideEmptyDataPoints = function() {
    var emptyDataPoints = this.filterRightSideDataPoints(
        this.identifyEmptyDataPoints()
    );
    this.removeDataPoints(emptyDataPoints.sort().reverse());
}

BarChart.prototype.filterRightSideDataPoints = function(indexes) {
    var righti = [];
    for (var i = this.labels.length-1; i >= 0; i--) {
        if (indexes.indexOf(i) < 0) {
            break;
        }
        righti.push(i);
    }
    return righti;
}


BarChart.prototype.removeDataset = function(id) {
    var index = this.indexOfDataset(id);
    if (index < 0) {
        throw "Dataset ID not found."; 
    }
    this.removeDatasetByIndex(index);
    this.chart.update();
}

BarChart.prototype.indexOfDataset = function(id) {
    var datasets = this.datasets;
    for (var i = 0; i < datasets.length; i++) {
        if (datasets[i].id === id) {
            return i;
        }
    }
    return -1;
}

BarChart.prototype.removeDatasetByIndex = function(index) {
    this.datasets.splice(index, 1);
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