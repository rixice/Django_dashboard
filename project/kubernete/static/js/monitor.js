window.onload = function () {

    document.getElementById('monitor').style.borderRightWidth = '10px';
    document.getElementById('monitor').style.borderRightStyle = 'solid';
    document.getElementById('monitor').style.borderRightColor = 'rgba(25,25,112,1)';
    document.getElementById('monitor').style.backgroundColor = 'rgba(25,25,112,0.6)' ;
    document.getElementById('monitor').style.width = '200px';

    var cpuChart = echarts.init(document.getElementById('cpu_status'));
    var memChart = echarts.init(document.getElementById('mem_status'));
    var processChart = echarts.init(document.getElementById('process_status'));


    // 指定图表的配置项和数据
        var cpu = {
            series: [{
                type: 'gauge',
                detail: {
                    formatter: 'CPU占用率 {value} %',
                    textStyle:{
                        fontSize:15
                    },
                },
                data: [{
                    value: [],
                }]
            }]
//            animationDurationUpdate: 1,
//            color:["gray"],
//            backgroundColor:['transparent'],
//            title: {
//                text: ' CPU',
//                textStyle: {
//                    color: "#228B22",
//                    fontSize: 21,
//                },
//            },
//            xAxis: {
//                name: "时间",
//                data: [],
//                boundaryGap: false,   //从y轴开始画
//                axisTick: {   //取消刻度线
//                    show: false
//                },
//                axisLabel: {    //取消刻度
//                    show: false
//                },
//            },
//            dataZoom: [
//                {
//                    type:'inside',
//                    show: true,
//                },
//            ],
//            yAxis: {
//                name: "占用率%",
//                splitLine: {
//                    show: false
//                },
//                max: 100,
//                min: 0,
//                interval: 20,
//            },
//            series: [{
//                type: 'line',
//                data: [],
//                symbol: 'none',
//                smooth: true,
//            }]
        };
/////////////////////////////////////////////////////////////////
        var mem = {
            series: [{
                type: 'gauge',
                detail: {
                    formatter: '内存使用率 {value} %',
                    textStyle:{
                        fontSize:15
                    },
                },
                data: [{
                    value: [],
                }]
            }]
//            animationDurationUpdate: 1,
//            color:["gray"],
//            backgroundColor:['transparent'],
//            title: {
//                text: ' 内存',
//                textStyle: {
//                    color: "#228B22",
//                    fontSize: 21,
//                },
//            },
//            tooltip: {},
//            legend: {
//            },
//            xAxis: {
//                name: "时间",
//                data: [],
//                boundaryGap: false,
//                axisTick: {
//                    show: false
//                },
//                axisLabel: {    //取消刻度
//                    show: false
//                },
//            },
//            yAxis: {
//                name: "使用率%",
//                splitLine: {
//                    show: false
//                },
//                max: 100,
//                min: 0,
//                interval: 20,
//            },
//            series: [{
//                type: 'line',
//                data: [],
//                symbol: 'none',
//                smooth: true,
//            }]
        };
////////////////////////////////////////////////////////////////
        var process = {
            animationDurationUpdate: 1,
            color:["gray"],
            backgroundColor:['transparent'],
            title: {
                text: 'CPU占用最高_进程',
                subtext: [],
                subtextStyle: {
                    color: "#6A5ACD",
                    fontSize: 18,
                },
                textStyle: {
                    color: "#228B22",
                    fontSize: 21,
                },
            },
            legend: {
                data: ['进程名称']
            },
            xAxis: {
                name: "时间",
                data: [],
                boundaryGap: false,
            },
            grid: {
                top: 90,
                left: 40,
            },
            yAxis: {
                name: "CPU使用率%",
                splitLine: {
                    show: false
                },
                type: 'value',
                max: 100,
                min: 0,
                interval: 20,
            },
            series: [{
                showAllSymbol: true,
                type: 'line',
                data: [],
                symbol: 'none',
                smooth: true,
            }]
        };

    var num_List_cpu = [0]
    var num_List_mem = [0]
    var num_List_pro_cpu = ['','','','','','','','','',0]

    function getList_cpu() {
        $.ajax({
            url: 'monitor',
            type: 'POST',
            dataType:"json",
            success: function (data1) {
                num_List_cpu.push(data1.datas.num1);
                if(num_List_cpu.length>1){
                    num_List_cpu.shift();
                }
                cpu.series[0].data = num_List_cpu;
                cpuChart.setOption(cpu);
            }
        })
    }
    function getList_mem() {
        $.ajax({
            url: 'monitor',
            type: 'POST',
            dataType:"json",
            success: function (data2) {
                num_List_mem.push(data2.datas.num2);
                if(num_List_mem.length>1){
                    num_List_mem.shift();
                }
                mem.series[0].data = num_List_mem;
                memChart.setOption(mem);
            }
        })
    }
    function getList_pro() {
        $.ajax({
            url: 'monitor',
            type: 'POST',
            dataType:"json",
            success: function (data3) {
                num_List_pro_cpu.push(data3.datas.num4);
                if(num_List_pro_cpu.length>10){
                    num_List_pro_cpu.shift();
                }
                process.title.subtext = data3.datas.num3;
                process.series[0].data = num_List_pro_cpu;
                processChart.setOption(process);
            }
        })
    }

    //初始化图表
    cpuChart.setOption(cpu);
    memChart.setOption(mem);
    processChart.setOption(process);

    time_cpu = setInterval(getList_cpu, 3000);
    time_mem = setInterval(getList_mem, 3000);
    time_pro = setInterval(getList_pro, 3000);
}