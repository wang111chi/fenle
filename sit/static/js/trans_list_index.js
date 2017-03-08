$(document).ready(function(){
	// 1. init jqgrid
	pageInit();

	// 2. error 确认
	$('.error_button').click(function(){
		$('.mask').hide();
		$('.error_area').hide();
		$('.error_content').html('');
	});

	// 3. 退款取消
	$('#confirm_drawback .confirm_btn_right').click(function(){
		hideDrawback();
	});
	

	// 4. 撤销取消
	$('#confirm_cancel .confirm_btn_right').click(function(){
		hideCancel();
	});

	// 5. 详情返回
	$('#order-detail .order_btn').click(function(){
		// 清空预授权完成input value
		$('#amount').val('');
		$('#bank_validcode').val('');

		// 隐藏详情，返回业务流水
		hideDetail();
	});
});


// award_feedback
return_data = {};

// page
var page_check = $('#check');
var page_od_detail = $('#order-detail');
var page_preaward_submit = $('#pre-award-submit');

// detail_message
var msg_od_detail = $('#order-detail .message');

//var dt_spid = $('.dt_spid');
var dt_product = $('.dt_product');
var dt_id = $('.dt_id');
var dt_modify_time = $('.dt_modify_time');
var dt_bank_type = $('.dt_bank_type');
var dt_bankacc_no = $('.dt_bankacc_no');
var dt_valid_date = $('.dt_valid_date');
var dt_status = $('.dt_status');
var dt_amount = $('.dt_amount');
var dt_jf_deduct_money = $('.dt_jf_deduct_money');
var dt_div_term = $('.dt_div_term');

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
		url : '/trans/list/data',//组件创建完成之后请求数据的url
		datatype : "json",//请求数据返回的类型。可选json,xml,txt
		colNames : [ '业务类型', '创建时间', '单号', '支付账户', '交易状态','订单金额', '' ],//jqGrid的列显示名字
		formatter:{
			number : {decimalSeparator:".", thousandsSeparator: " ", decimalPlaces: 2, defaultValue: '0.00'},
		},
		colModel : [ //jqGrid每一列的配置信息。包括名字，索引，宽度,对齐方式.....
			{label : '业务类型', classes : 'product',name : 'product',width:130, align : "center",sortable : false, title : false,formatter:fmatterServiceType}, 
			{label : '创建时间', name : 'create_time', width:160, align : "center",sortable : false, title : false}, 
			{label : '单号', width:250, name : 'id', align : "center",sortable : false, title : false}, 
			{label : '支付账户', name : 'bankacc_no', align : "center", width : 150, sortable : false, title : false}, 
			{label : '交易状态', classes:'status',name : 'status', formatter:fmatterStatus, align : "center",width : 80, sortable : false, title : false}, 
			{label : '订单金额', name : 'amount', formatter:'number', align : "center", width : 100, sortable : false, title : false}, 
			{label :'操作', name : 'bank_list', formatter:fmatterOperation, align : "center", width : 130,sortable : false, title : false} 
		],
		rowNum:1000,
		mtype : "get",//向后台请求数据的ajax的类型。可选post,get
	});
}



/************ 1. fomatter ************/
// formatter 业务类型 
function fmatterServiceType(cellvalue){
	if (cellvalue == 1) {
		return '分期';
	} else if (cellvalue == 2){
		return '纯积分';
	} else if (cellvalue == 3){
		return '积分+现金';
	} else if (cellvalue == 4){
		return '无卡订购';
	} else if (cellvalue == 5){
		return '预授权';
	} else if (cellvalue == 6){
		return '预授权完成';
	} else {
		return 'ERROR'
	}
}


// formatter 交易状态
function fmatterStatus(cellvalue){
	if (cellvalue == 0) {
		return '支付中';
	} else if (cellvalue == 1){
		return '成功';
	} else if (cellvalue == 2){
		return '失败';
	} else if (cellvalue == 3){
		return '已撤销';
	} else if (cellvalue == 4){
		return '已退款';
	} else {
		return 'ERROR';
	}
}


// formatter 操作
function fmatterOperation(cellvalue, options, rowObject){
	
	
	if (rowObject.status == 1 && rowObject.product == 5){

		// 预授权 -- 成功 -- 查看(可提交实际金额) 退款 撤销
		// 查看参数 : bank_list, id, bankacc_no, valid_date, mobile 
		return "<a class=\"trans\" href=\"javascript:preauthDetail('" + rowObject.bank_list + "','" + rowObject.id + "','" + rowObject.bankacc_no + "','" + rowObject.valid_date + "','" + rowObject.mobile + "')\">查看</a> | <a class=\"refund\" href=\"javascript:applyDrawback('" + rowObject.product + "','" + rowObject.amount + "','" + rowObject.bankacc_no + "','" + rowObject.bank_list + "')\">退款</a> | <a class=\"cancel\" href=\"javascript:cancel('"  + rowObject.product + "','" + rowObject.bank_list + "')\">撤销</a>";

	} else if (rowObject.status == 1){

		// 分期/纯积分/积分+现金/无卡订购/预授权完成 -- 成功 -- 查看 退款 撤销
		return "<a class=\"trans\" href=\"javascript:getDetail('" + rowObject.bank_list + "')\">查看</a> | <a class=\"refund\" href=\"javascript:applyDrawback('" + rowObject.product + "','" + rowObject.amount + "','" + rowObject.bankacc_no + "','" + rowObject.bank_list + "')\">退款</a> | <a class=\"cancel\" href=\"javascript:cancel('" + rowObject.product + "','" + rowObject.bank_list + "')\">撤销</a>";

	} else {

		// 全部产品 -- 支付中/失败/已撤销/已退款/error -- 查看
		return "<a class=\"trans\" href=\"javascript:getDetail('" + rowObject.bank_list + "')\">查看</a>";
	}
}




/************ 2. 退款 ************/
// 退款
function applyDrawback(product, amount, bankacc_no, bank_list){

	// 弹框 请注意，XX元将直接退回信用卡XXX账户！
	drawback_content.html( '请注意！' + amount + '元将退回信用卡' + bankacc_no + '账户！');
	mask.show();
	drawback_box.show();

	console.log(product);
	// 绑定确定事件
	drawback_btn_left.unbind();
	drawback_btn_left.click(function(){

		sendDrawback('/trans/refund',bank_list);
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
				showMsg('退款提交成功');
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


function hideDrawback(){
	mask.hide();
	drawback_box.hide();
	return false;
}




/************ 3. 撤销 ************/
// 撤销
function cancel(product, bank_list){
	// 弹框
	cancel_content.html('订单将撤销');
	mask.show();
	cancel_box.show();

	// 绑定确定事件
	cancel_btn_left.unbind();
	cancel_btn_left.click(function(){

		sendCancel('/trans/cancel', bank_list);
		
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
				showMsg('撤销提交成功');
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


function hideCancel(){
	mask.hide();
	cancel_box.hide();
	return false;
}




/************ 4. 查看详情 ************/
// 订单详情
function getDetail(bank_list){

	// 2. post详情
	$.ajax({
		type:'GET',
		url:'/trans',
		data:{"bank_list":bank_list},
		success:function(data){

			if ( data.status == 0 ){
				showDetail(data.trans);
			} else if ( data.status == 1 ){
				showMsg(data.message);
			} else {
				showMsg('ERROR');
			}
		},
		error:function(){
			showMsg('服务器繁忙，请稍后重试');
		}
	});
}

// 显示详情
function showDetail(data){
	// data.status转义
	if ( data.status == 0 ) {
		data.status = '支付中';
	} else if (data.status == 1 ) {
		data.status = '成功'; 
	} else if (data.status == 2 ){
		data.status = '失败';
	} else if (data.status == 3 ){
		data.status = '已撤销';
	} else if (data.status == 4 ){
		data.status = '已退款'; 
	} else {
		data.stauts ='Error'
	}

	// data.product 转义
	if ( data.product == 1 ) {
		data.product = '分期';
	} else if (data.product == 2 ) {
		data.product = '积分'; 
	} else if (data.product == 3 ){
		data.product = '积分+分期';
	} else if (data.product == 4 ){
		data.product = '普通信用卡消费';
	} else if (data.product == 5 ){
		data.product = '预授权';
	} else if (data.product == 6){
		data.product = '预授权完成';
	} else {
		data.product = 'ERROR'; 
	}

	// 填充详情
	dt_product.html(data.product);
	dt_id.html(data.id);
	dt_modify_time.html(data.modify_time);
	dt_bank_type.html(data.bank_type);
	dt_bankacc_no.html(data.bankacc_no);
	dt_valid_date.html(data.valid_date);
	dt_status.html(data.status);
	dt_amount.html(data.amount);
	dt_jf_deduct_money.html(data.jf_deduct_money);
	dt_div_term.html(data.div_term);

	// 展示详情页
	page_check.hide();
	page_od_detail.show();
}

// 隐藏详情
function hideDetail(){
	dt_product.html('');
	dt_id.html('');
	dt_modify_time.html('');
	dt_bank_type.html('');
	dt_bankacc_no.html('');
	dt_valid_date.html('');
	dt_status.html('');
	dt_amount.html('');
	dt_jf_deduct_money.html('');
	dt_div_term.html('');

	// 隐藏详情页,展示查询页
	page_od_detail.hide();
	page_preaward_submit.hide();
	page_check.show();

	return false;
}



/************ 5. 预授权完成 ************/
// 预授权-成功 -- 查看详情，完成预授权

// 已有参数 : bank_list, id, bankacc_no, valid_date, mobile 
// 填写参数 : amount, bank_validcode

// 查看详情 : bank_list
// 验证码发送 : bankacc_no, valid_date, mobile, amount
// 预授权完成 : (bank_list, bank_sms_time) bankacc_no, valid_date, mobile, amount, bank_validcode, id

return_data = {};
function preauthDetail(bank_list, id, bankacc_no, valid_date, mobile){

	console.log(bank_list);
	console.log(id);
	console.log(bankacc_no);
	console.log(valid_date);
	console.log(mobile);

	// post详情
	$.ajax({
		type:'GET',
		url:'/trans',
		data:{"bank_list":bank_list},
		success:function(data){

			if ( data.status == 0 ){
				// 预授权完成
				showDetail(data.trans);
				page_preaward_submit.show();

				// 解绑之前的事件
				return_data = {};
				$('#send_captcha').unbind();
				$('#submit').unbind();

				// 绑定，提交事件
				preauthSubmit(bank_list, id, bankacc_no, valid_date, mobile);

			} else if ( data.status == 1 ){
				showMsg(data.message);
			} else {
				showMsg('ERROR');
			}
		},
		error:function(){
			showMsg('服务器繁忙，请稍后重试');
		}
	});
}


// 绑定 预授权完成 事件
function preauthSubmit(bank_list, id, bankacc_no, valid_date, mobile){
	// 1. 发送验证码

	$('#send_captcha').click(function(){

		return_data = {};

		// 1-1 获取要素
		var bank_spid = $('#bank_spid').val();
		var terminal_id = $('#terminal_id').val();

		var amount = $('#amount').val();
		var captcha_data = {'bank_spid':bank_spid, 'terminal_id':terminal_id, 'amount':amount, 'bankacc_no':bankacc_no, 'valid_date':valid_date, 'mobile':mobile};

		// 1-2 post
		sendCaptcha('/sms/send', captcha_data);
	});

	// 2. 提交
	$('#submit').click(function(){

		if (!checkEmpty(return_data.bank_list,'请先发送验证码')) return false;
		if (!checkEmpty(return_data.bank_sms_time,'请先发送验证码')) return false;

		// 2-1 获取要素
		var bank_spid = $('#bank_spid').val();
		var terminal_id = $('#terminal_id').val();

		var amount = $('#amount').val();
		var bank_validcode = $('#bank_validcode').val();


		var submit_data = $.extend(return_data, {'bank_spid':bank_spid, 'terminal_id':terminal_id, 'amount':amount, 'bankacc_no':bankacc_no, 'valid_date':valid_date, 'mobile':mobile, 'bank_validcode':bank_validcode, 'parent_id':id});

		// 2-3 post
		submitForm('/preauth/done', submit_data);
	});	
}

function checkEmpty(text,show_msg){
	if (text == '' || text == undefined || text == null) {
		showMsg(show_msg);
		return false;
	} else {
		return true;
	}
}


// 短信验证码
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


// 提交表单 预授权完成
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
				showMsg('ERROR');
			}
		},
		error:function(){
			showMsg('服务端错误，请稍后重试');
		}
	});
}




/************ showMsg ************/
function showMsg(msg){
	$('.mask').show();
	$('.error_area').show();
	$('.error_content').html(msg);
}
