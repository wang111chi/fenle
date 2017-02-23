var Util = (function(){
	var return_data = {};
	function showMsg(msg){
		$('.mask').show();
		$('.error_area').show();
		$('.error_content').html(msg);
	}

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
					showMsg('发送成功');
				} else if (data.status == 1){
					showMsg(data.message);
				} else {
					showMsg('其他信息');
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

	$('.error_button').click(function(){
		$('.mask').hide();
		$('.error_area').hide();
		$('.error_content').html('');
	});

	return {
		showMsg:showMsg,
		sendCaptcha:sendCaptcha
	}
})();
