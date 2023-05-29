function password_view(password_id,btn_id){

	// (1)パスワード入力欄とボタンのHTMLを取得
	let btn_passview = document.getElementById(btn_id);
	let input_pass = document.getElementById(password_id);

    // (2)パスワード入力欄のtype属性を確認
    console.log(input_pass)
    if( input_pass.type === 'password' ) {

        // (3)パスワードを表示する
        input_pass.type = 'text';
        btn_passview.textContent = '非表示';

    } else {

        // (4)パスワードを非表示にする
        input_pass.type = 'password';
        btn_passview.textContent = '表示';
    }
	

};