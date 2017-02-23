function showMsg(msg){
	$('.mask').show();
	$('.error_area').show();
	$('.error_content').html(msg);
}

// 发送短信验证码
function sendCaptcha(url, captcha_data){
	$.ajax({
		url:url,
		type:'POST',
		data:captcha_data,
		success:function(data){

			// 1-3 显示返回内容

			var feedback = '【发送验证码】<br>';
			for(i in data){
				feedback += i + ':' + data[i] +'<br>';
			}
			$('#feedback').html(feedback);

			
			if (data.status == 0){
				showMsg('提交成功');
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
			showMsg('请求未发出');
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

			// 2-4显示返回内容
			var feedback = '【提交】<br>';
			for(i in data){
				feedback += i + ':' + data[i] +'<br>';
			}
			$('#feedback').html(feedback);

			if (data.status == 0){
				showMsg('提交成功');
			} else if (data.status == 1){
				showMsg(data.message);
			} else {
				showMsg('其他信息');
			}


		},
		error:function(){
			showMsg('请求未发出');
		}
	});
}

// 绑定弹框确定按钮
function hideBox(){
	$('.mask').hide();
	$('.error_area').hide();
	$('.error_content').html('');
}