$(document).ready(function(){
	// 1. init jqgrid
	pageInit();

	// 2. error 确认按钮
	$('.error_button').click(function(){
		$('.mask').hide();
		$('.error_area').hide();
		$('.error_content').html('');
	});

	// 3. 退款取消按钮
	$('#confirm_drawback .confirm_btn_right').click(function(){
		$('.mask').hide();
		$('#confirm_drawback').hide();
		return false;
	});
	

	// 4. 撤销取消事件
	$('#confirm_cancel .confirm_btn_right').click(function(){
		$('.mask').hide();
		$('#confirm_cancel').hide();
		return false;
	});

	// 5. 订单详情返回事件
	$('#order-detail .order_btn').click(function(){

		// 清空详情数据
		clearDetail();

		// 隐藏详情页,展示查询页
		page_od_detail.hide();
		page_preaward_submit.hide();
		page_check.show();

	});
});


// award_feedback
return_data = {};

// url
var url_waterbill = '/trans_list';  //流水
var url_od_detail = '/detail'; //订单详情


// page
var page_check = $('#check');
var page_od_detail = $('#order-detail');
var page_preaward_submit = $('#pre-award-submit');


// detail_message
var msg_od_detail = $('#order-detail .message');


var dt_spid = $('.dt_spid');
var dt_service_type = $('.dt_service_type');
var dt_order_num = $('.dt_order_num');
var dt_order_time = $('.dt_order_time');
var dt_pay_bank = $('.dt_pay_bank');
var dt_bankacc_no = $('.dt_bankacc_no');
var dt_valid_date = $('.dt_valid_date');
var dt_status = $('.dt_status');
var dt_amount = $('.dt_amount');
var dt_point_amount = $('.dt_point_amount');
var dt_crash_amount = $('.dt_crash_amount');
var dt_period = $('.dt_period');


// error
var mask = $('.mask');
var error_area = $('.error_area');
var error_content = $('.error_content');
var error_btn = $('.error_button');

// 退款confirm
var drawback_box = $('#confirm_drawback');
var drawback_content = $('#confirm_drawback .confirm_content');
var drawback_btn_left = $('#confirm_drawback .confirm_btn_left');

// 撤销confirm
var cancel_box = $('#confirm_cancel');
var cancel_content = $('#confirm_cancel .confirm_content');
var cancel_btn_left = $('#confirm_cancel .confirm_btn_left');

// 1. jqgrid
function pageInit(){
	//创建jqGrid组件
	jQuery("#list").jqGrid({
		url : url_waterbill,//组件创建完成之后请求数据的url
		datatype : "json",//请求数据返回的类型。可选json,xml,txt
		colNames : [ '业务类型', '创建时间', '单号', '支付账户', '交易状态','订单金额', '' ],//jqGrid的列显示名字
		formatter:{
			number : {decimalSeparator:".", thousandsSeparator: " ", decimalPlaces: 2, defaultValue: '0.00'},
		},
		colModel : [ //jqGrid每一列的配置信息。包括名字，索引，宽度,对齐方式.....
			{label : '业务类型', name : 'product',width:130, align : "center",sortable : false, title : false,formatter:fmatterServiceType}, 
			{label : '创建时间', name : 'create_time', width:160, align : "center",sortable : false, title : false}, 
			{label : '单号', width:250, name : 'id', align : "center",sortable : false, title : false}, 
			{label : '支付账户', name : 'bankacc_no', align : "center", width : 150, sortable : false, title : false}, 
			{label : '交易状态', name : 'status', formatter:fmatterStatus, align : "center",width : 80, sortable : false, title : false}, 
			{label : '订单金额', name : 'amount', formatter:'number', align : "center", width : 100, sortable : false, title : false}, 
			{label :'操作', name : 'bank_list', formatter:fmatterDetail, align : "center", width : 130,sortable : false, title : false} 
		],
		rowNum:1000,
		mtype : "post",//向后台请求数据的ajax的类型。可选post,get
	});
}


// 1. formatter 业务类型 
function fmatterServiceType(cellvalue){
	if (cellvalue == 1) {
		return '分期';
	} else if (cellvalue == 2){
		return '纯积分';
	} else if (cellvalue == 3){
		return '积分+现金';
	} else if (cellvalue == 4){
		return '无卡订购';
	} else {
		return 'ERROR'
	}
}


// 2. formatter 交易状态
function fmatterStatus(cellvalue){
	if (cellvalue == 0) {
		return '支付中';
	} else if (cellvalue == 1){
		// 支付成功
		return '成功';
	} else if (cellvalue == 2){
		// 支付失败
		return '失败';
	} else if (cellvalue == 3){
		return '已撤销';
	} else if (cellvalue == 4){
		return '已退款';
	} else {
		return 'ERROR';
	}
}


// 3. formatter 操作
function fmatterDetail(cellvalue, options, rowObject){
	// 判断 业务类型 是否为 预授权
	
	// 成功
	if (rowObject.status == 1){
		if ( rowObject.product == 5){

			// 预授权
			return "<a href=\"javascript:getAwardDetail('" + rowObject.bank_list + "')\">查看</a> | <a href=\"javascript:applyDrawback('" rowObject.product + "','" + rowObject.amount + "','" + rowObject.bankacc_no + "','" + rowObject.bank_list+ "')\">退款</a> | <a href=\"javascript:cancel('" rowObject.product + "','" + rowObject.bank_list + "')\">撤销</a>";
		} else {

			// 非预授权
			return "<a href=\"javascript:getDetail('" + rowObject.bank_list + "')\">查看</a> | <a href=\"javascript:applyDrawback('" rowObject.product + "','" + rowObject.amount + "','" + rowObject.bankacc_no + "','" + rowObject.bank_list+ "')\">退款</a> | <a href=\"javascript:cancel('" rowObject.product + "','" + rowObject.bank_list + "')\">撤销</a>";
		}
	} else {
		return "<a href=\"javascript:getDetail('" + rowObject.bank_list + "')\">查看</a>";
	}
}


// 3-2 操作 -- 退款
function applyDrawback(product, amount, bankacc_no, bank_list){

	// 弹框 请注意，XX元将直接退回信用卡XXX账户！
	drawback_content.html( '请注意！' + amount + '元将退回信用卡' + bankacc_no + '账户！');
	mask.show();
	drawback_box.show();

	// 绑定确定事件
	drawback_btn_left.click(function(product, bank_list){

		// post退款 1:分期，2：积分，3：积分+现金，4：普通信用卡消费
		if ( product == 1) {
			sendDrawback('/layaway/drawback', bank_list);
		} else if ( product == 2 ) {
			sendDrawback('/poit/drawback', bank_list);
		} else if ( product == 3 ) {
			sendDrawback('/point_cash/drawback', bank_list);
		} else if ( product == 4 ) {
			sendDrawback('/consume/drawback', bank_list);
		} else {
			showMsg('ERROR,该产品类型未定义')
		}
	});
}


// 退款 POST
function sendDrawback(url, bank_list){
	$.ajax({
		type:'POST',
		url:url,
		data:{"bank_list":bank_list},
		success:function(data) {

			hideDrawback();
			if (data.status == 0){
				showMsg('发送成功');
			} else if (data.status == 1){
				showMsg(data.message);
			} else {
				showMsg('ERROR');
			}
		},
		error:function(){
			hideDrawback();
			showMsg('服务器繁忙，请稍后重试');
		}
	});
}


// 3-3 操作 -- 撤销
function cancel(product, bank_list){
	// 弹框
	cancel_content.html('订单' + order_num + '将撤销');
	mask.show();
	cancel_box.show();

	// 绑定确定事件
	cancel_btn_left.click(function(product, bank_list){

		// post撤销 1:分期，2：积分，3：积分+现金，4：普通信用卡消费
		if ( product == 1) {
			sendCancel('/layaway/cancel', bank_list);
		} else if ( product == 2 ) {
			sendCancel('/poit/cancel', bank_list);
		} else if ( product == 3 ) {
			sendCancel('/point_cash/cancel', bank_list);
		} else if ( product == 4 ) {
			sendCancel('/consume/cancel', bank_list);
		} else {
			showMsg('ERROR,该产品类型未定义')
		}
		
	});
}

// 撤销 POST
function sendCancel(url, bank_list){
	$.ajax({
		type:'POST',
		url:url,
		data:{"bank_list":bank_list},
		success:function(data) {

			hideCancel();
			if (data.status == 0){
				showMsg('发送成功');
			} else if (data.status == 1){
				showMsg(data.message);
			} else {
				showMsg('ERROR');
			}
		},
		error:function(){
			hideCancel();
			showMsg('服务器繁忙，请稍后重试');
		}
	});
}


// 3-1 操作 -- 查看订单详情
function getDetail(bank_list){

	// 1. 隐藏查询页，展示详情页
	page_check.hide();
	page_od_detail.show();


	// 2. post订单详情,展示返回json
	$.post(url_od_detail, {'bank_list':bank_list}, function(data){

		// 显示详情
		showDetail(data);
	});
}


// 3-4 操作 -- 查看（预授权）订单详情，并提交实际金额
function getAwardDetail(bank_list){
	//console.log(order_num);

	// 1. 隐藏查询页，展示详情页,预授权提单
	page_check.hide();
	page_od_detail.show();
	page_preaward_submit.show();


	// 2. post详情
	$.post(url_od_detail,{'bank_list':bank_list}, function(data){

		// 显示详情
		showDetail(data);
	});

	// 3. 绑定 -- 提交实际金额事件
	preAwardSubmit(bank_list);

	
}


// 预授权提单
return_data = {};

function preAwardSubmit(bank_list){
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
		sendCaptcha('/sms/send', captcha_data);
	});

	// 2. 提交
	$('#submit').click(function(){

		// 2-1 获取要素
		var amount = $('#amount').val();
		var bankacc_no = $('#bankacc_no').val();
		var valid_date = $('#valid_date').val();
		var mobile = $('#mobile').val();
		var bank_validcode = $('#bank_validcode').val();

		// 2-2 返回return_data/订单要素/表单要素
		var submit_data = $.extend(return_data, {'bank_list':bank_list}, {'amount':amount, 'bankacc_no':bankacc_no, 'valid_date':valid_date, 'mobile':mobile, 'bank_validcode':bank_validcode});

		// 2-3 post
		submitForm('/award/trade', submit_data);
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




// 显示详情
function showDetail(data){
	dt_spid.html(data.spid);
	dt_service_type.html(data.service_type);
	dt_order_num.html(data.order_num);
	dt_order_time.html(data.order_time);
	dt_pay_bank.html(data.pay_bank);
	dt_bankacc_no.html(data.bankacc_no);
	dt_valid_date.html(data.valid_date);
	dt_status.html(data.status);
	dt_amount.html(data.amount);
	dt_point_amount.html(data.point_amount);
	dt_crash_amount.html(data.crash_amount);
	dt_period.html(data.period);
}


// 清楚详情内容
function clearDetail(){
	dt_spid.html('');
	dt_service_type.html('');
	dt_order_num.html('');
	dt_order_time.html('');
	dt_pay_bank.html('');
	dt_bankacc_no.html('');
	dt_valid_date.html('');
	dt_status.html('');
	dt_amount.html('');
	dt_point_amount.html('');
	dt_crash_amount.html('');
	dt_period.html('');
}

function showMsg(msg){
	$('.mask').show();
	$('.error_area').show();
	$('.error_content').html(msg);
}


// common.js
// 发送短信验证码
function sendCaptcha(url, captcha_data){
	$.ajax({
		url:url,
		type:'POST',
		data:captcha_data,
		success:function(data){

			if (data.status == 0){
				showMsg('发送成功');
			} else if (data.status == 1){
				showMsg(data.message);
			} else {
				showMsg('ERROR');
			}

			// 1-4 将返回的bank_list和bank_sms_time存起

			return_data.bank_list = data.bank_list;
			return_data.bank_sms_time = data.bank_sms_time;

		},
		error:function(){
			showMsg('服务端错误，请稍后重试');
		}
	});
}

// 提交表单
function submitForm(url, submit_data){
	$.ajax({
		url:url,
		type:'POST',
		data:submit_data,
		success:function(data){
			if (data.status == 0){
				showMsg('提交成功');
			} else if (data.status == 1){
				showMsg(data.message);
			} else {
				showMsg('其他信息');
			}


		},
		error:function(){
			showMsg('服务端错误，请稍后重试');
		}
	});
}

