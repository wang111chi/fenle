$(function(){
	// 页面加载后，加载交易订单table
	$(document).ready(function(){
		// 1. init jqgrid
		pageInit();

		// 3. 绑定确认按钮
		$('.error_button').click(function(){
			hideBox();
		});
	});
});

// ajax url 

var url_waterbill = '/liushui';  //流水
var url_od_detail = '/detail'; //订单详情
var url_apply_drawback = '/applyDrawback'; // 退款
var url_apply_cancel = '/cancel';  // 撤销
var url_preaward_captcha = '/captcha'; // 预授权-验证码
var url_preaward_submit = '/captcha'; // 预授权- 提交


// page
var page_check = $('#check');
var page_od_detail = $('#order-detail');
var page_pre_award_detail = $('#pre-award-detail');

// detail_message
var msg_od_detail = $('#order-detail .message');
var msg_preaward_detail = $('#pre-award-detail .message');



// btn
var btn_od_detail = $('#order-detail .order_btn');
var btn_preaward_detail = $('#pre-award-detail .order_btn');

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
				url : url_waterbill,//组件创建完成之后请求数据的url
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
				rowNum:1000,
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
		return '成功';
	} else if (cellvalue == 2){
		return '失败';
	} else if (cellvalue == 3){
		return '已撤销';
	} else if (cellvalue == 4){
		return '已退款';
	} else if (cellvalue == 5){
		return '已完成';
	} else {
		return 'ERROR';
	}
}

// 3. formatter 操作
function fmatterDetail(cellvalue, options, rowObject){
	// 判断 业务类型 是否为 预授权
	
	// 成功
	if (rowObject.status == 1){
		if ( rowObject.service_type == 5){

			// 预授权
			return "<a href=\"javascript:getPreAwardDetail('" + rowObject.order_num + "')\">查看</a> | <a href=\"javascript:applyDrawback('" + rowObject.total_fee + "','" + rowObject.card + "','" + rowObject.order_num+ "')\">退款</a> | <a href=\"javascript:cancel('" + rowObject.order_num + "')\">撤销</a>";
		} else {

			// 非预授权
			return "<a href=\"javascript:getDetail('" + rowObject.order_num + "')\">查看</a> | <a href=\"javascript:applyDrawback('" + rowObject.total_fee + "','" + rowObject.card + "','" + rowObject.order_num+ "')\">退款</a> | <a href=\"javascript:cancel('" + rowObject.order_num + "')\">撤销</a>";
		}
	} else {
		return "<a href=\"javascript:getDetail('" + rowObject.order_num + "')\">查看</a>";
	}

}


// 3-1 操作 -- 查看订单详情
function getDetail(ordernum){

	// 隐藏查询页，展示详情页
	page_check.hide();
	page_od_detail.show();

	// post订单详情,展示返回json
	$.post(url_od_detail, {'ordernum':ordernum}, function(data){

		var detail = '';
		for(i in data){
			detail += i + ':' + data[i] +'<br>';
		}
		msg_od_detail.html(detail);
	});

	// 绑定返回事件
	btn_od_detail.click(function(){
		// 清空详情数据
		msg_od_detail.html('');

		// 隐藏详情页,展示查询页
		page_od_detail.hide();
		page_check.show();
	});	
}


/* 3-2 操作 -- 查看退款详情
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

*/


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
			url:url_apply_drawback,
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
			url:url_apply_cancel,
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

// 3-4 操作 -- 查看（预授权）订单详情，并提交实际金额
function getPreAwardDetail(order_num){
	console.log(order_num);

	// 1. 隐藏查询页，展示详情页
	page_check.hide();
	page_pre_award_detail.show();

	// post订单详情,展示返回json
	$.post(url_od_detail,{'ordernum':order_num}, function(data){

		var detail = '';
		for(i in data){
			detail += i + ':' + data[i] +'<br>';
		}
		msg_preaward_detail.html(detail);
	});

	// 2. 绑定 -- 提交实际金额事件
	preAwardSubmit(order_num);

	// 3. 绑定返回事件
	btn_preaward_detail.click(function(){
		// 清空详情数据
		msg_preaward_detail.html('');

		// 隐藏详情页,展示查询页
		page_pre_award_detail.hide();
		page_check.show();
	});	
}

// 预授权提单
var return_data = {};
function preAwardSubmit(order_num){
	// 1. 发送验证码

	$('#send_captcha').click(function(){

		return_data = {};

		// 1-1 获取要素
		var amount = $('#amount').val();
		var valid_date = $('#valid_date').val();
		var bankacc_no = $('#bankacc_no').val();
		var mobile = $('#mobile').val();

		// 提交表单要素
		var captcha_data = {'amount':amount, 'bankacc_no':bankacc_no, 'valid_date':valid_date, 'mobile':mobile};

		// 1-2 post
		sendCaptcha(url_preaward_captcha, captcha_data);
	});

	// 2. 提交
	$('#submit').click(function(){

		// 2-1 获取要素
		var amount = $('#amount').val();
		var bankacc_no = $('#bankacc_no').val();
		var valid_date = $('#valid_date').val();
		var mobile = $('#mobile').val();
		var captcha = $('#captcha').val();

		// 2-2 返回return_data/订单要素/表单要素
		var submit_data = $.extend(return_data, {'order_num':order_num}, {'amount':amount, 'bankacc_no':bankacc_no, 'valid_date':valid_date, 'mobile':mobile, 'captcha':captcha});

		// 2-3 post
		submitForm(url_preaward_submit, submit_data);
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