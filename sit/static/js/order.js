$(function(){
	// 页面加载后，加载交易订单table
	$(document).ready(function(){
		// 1. init jqgrid
		pageInit();
	});
});

// section元素:查询页，订单详情，退款详情
var page_check = $('#check');
var page_od_detail = $('#order-detail');

// btn
var btn_od_detail = $('#order_btn');

// error
var mask = $('.mask');
var error_area = $('.error_area');
var error_content = $('.error_content');
var error_btn = $('.error_button');

// 退款confirm
var drawback_box = $('#confirm_drawback');
var drawback_content = $('#confirm_drawback .confirm_content');
var drawback_btn_left = $('#confirm_drawback .confirm_btn_left');
var drawback_btn_right = $('#confirm_drawback .confirm_btn_right');

// 撤销confirm
var cancel_box = $('#confirm_cancel');
var cancel_content = $('#confirm_cancel .confirm_content');
var cancel_btn_left = $('#confirm_cancel .confirm_btn_left');
var cancel_btn_right = $('#confirm_cancel .confirm_btn_right');

// 1. jqgrid
function pageInit(){
	//创建jqGrid组件
	jQuery("#list").jqGrid(
			{
				url : '/liushui',//组件创建完成之后请求数据的url
				datatype : "json",//请求数据返回的类型。可选json,xml,txt
				colNames : [ '业务类型', '创建时间', '单号', '支付账户', '交易状态','订单金额', '' ],//jqGrid的列显示名字
				formatter:{
					number : {decimalSeparator:".", thousandsSeparator: " ", decimalPlaces: 2, defaultValue: '0.00'},
				},
				colModel : [ //jqGrid每一列的配置信息。包括名字，索引，宽度,对齐方式.....
					{label : '业务类型', name : 'service_type',width:130, align : "center",sortable : false, title : false,formatter:fmatterServiceType}, 
					{label : '创建时间', name : 'create_time', width:160, align : "center",sortable : false, title : false}, 
					{label : '单号', width:250, name : 'order_num', align : "center",sortable : false, title : false}, 
					{label : '支付账户', name : 'card', align : "center", width : 150, sortable : false, title : false}, 
					{label : '交易状态', name : 'status', formatter:fmatterStatus, align : "center",width : 80, sortable : false, title : false}, 
					{label : '订单金额', name : 'total_fee', formatter:'number', align : "center", width : 100, sortable : false, title : false}, 
					{label :'操作', name : 'order_num', formatter:fmatterDetail, align : "center", width : 130,sortable : false, title : false} 
				],
				scroll:true,

				mtype : "post",//向后台请求数据的ajax的类型。可选post,get
			});
}

// 1. formatter 业务类型
function fmatterServiceType(cellvalue){
	if (cellvalue == 1) {
		return '纯积分';
	} else if (cellvalue == 2){
		return '积分+现金';
	} else if (cellvalue == 3){
		return '无卡订购';
	} else if (cellvalue == 4){
		return '分期';
	} else if (cellvalue == 5){
		return '预授权'
	} else {
		return 'ERROR';
	}
}

// 2. formatter 交易状态
function fmatterStatus(cellvalue){
	if (cellvalue == 1) {
		return '消费';
	} else if (cellvalue == 2){
		return '已撤销';
	} else if (cellvalue == 3){
		return '已经退款';
	} else {
		return 'ERROR';
	}
}

// 3. formatter 操作
function fmatterDetail(cellvalue, options, rowObject){
	return "<a href=\"javascript:getDetail('" + rowObject.order_num + "')\">查看</a> | <a href=\"javascript:applyDrawback('" + rowObject.total_fee + "','" + rowObject.card + "','" + rowObject.order_num+ "')\">退款</a> | <a href=\"javascript:cancel('" + rowObject.order_num + "')\">撤销</a>";
}



// 3-1 操作 -- 查看订单详情
function getDetail(ordernum){

	// 隐藏查询页，展示详情页
	page_check.hide();
	page_od_detail.show();

	// post订单详情,展示返回json
	$.post('/detail',{'ordernum':ordernum}, function(data){

		var detail = '';
		for(i in data){
			detail += i + ':' + data[i] +'<br>';
		}
		$('#detail-msg').html(detail);
	});

	// 绑定返回事件
	btn_od_detail.click(function(){
		// 清空详情数据
		$('#detail-msg').html('');

		// 隐藏详情页,展示查询页
		page_od_detail.hide();
		page_check.show();
	});	
}


// 3-2 操作 -- 查看退款详情
function getDrawbackDetail(ordernum){

	// 隐藏查询页，展示详情页
	page_check.hide();
	page_od_detail.show();

	// post订单详情,展示返回json
	$.post('/drawbackDetail',{'ordernum':ordernum}, function(data){

		var detail = '';
		for(i in data){
			detail += i + ':' + data[i] +'<br>';
		}
		$('#detail-msg').html(detail);
	});

	// 绑定返回事件
	btn_od_detail.click(function(){
		// 清空详情数据
		$('#detail-msg').html('');

		// 隐藏详情页,展示查询页
		page_od_detail.hide();
		page_check.show();
	});	
}


// 3-2 操作 -- 申请退款
function applyDrawback(total_fee, pay_card, order_num){

	// 弹框
	drawback_content.html('订单' + order_num + '将进行退款<br>订单金额为' + total_fee + '<br>付款账户为' + pay_card);
	mask.show();
	drawback_box.show();

	// 绑定确定事件
	drawback_btn_left.click(function(){

		// post退款事件
		$.ajax({
			type:'POST',
			url:'/applyDrawback',
			data:{"ordernum":order_num},
			success:function(data) {

				hideDrawback();
				var drawback_result = '【退款返回结果】<br>';
				for(i in data){
					// 显示退款返回结果
					drawback_result += i + ':' + data[i] +'<br>';
					showBox(drawback_result);
				}
			},
			error:function(){
				hideDrawback();
				showBox('网络出错，请检查网络');
			}
		});
	});

	//绑定取消事件
	drawback_btn_right.click(function(){
		mask.hide();
		drawback_box.hide();
		return false;
	});
}


// 3-3 操作 -- 撤销
function cancel(order_num){
	// 弹框
	cancel_content.html('订单' + order_num + '将撤销');
	mask.show();
	cancel_box.show();

	// 绑定确定事件
	cancel_btn_left.click(function(){

		// post退款事件
		$.ajax({
			type:'POST',
			url:'/cancel',
			data:{"ordernum":order_num},
			success:function(data) {

				hideCancel();
				var cancel_result = '【撤销返回结果】<br>';
				for(i in data){
					// 显示退款返回结果
					cancel_result += i + ':' + data[i] +'<br>';
					showBox(cancel_result);
				}
			},
			error:function(){
				hideCancel();
				showBox('网络出错，请检查网络');
			}
		});
	});

	//绑定取消事件
	cancel_btn_right.click(function(){
		mask.hide();
		cancel_box.hide();
		return false;
	});
}

function hideDrawback(){
	mask.hide();
	drawback_box.hide();
}

function hideCancel(){
	mask.hide();
	cancel_box.hide();
}

function showBox(msg){
	error_content.html(msg);
	mask.show();
	error_area.show();

	//绑定error确定事件
	error_btn.click(function(){
		error_content.html('');
		mask.hide();
		error_area.hide();
	});
}