const perms = {
    generalViewChannels: 1024,
    generalCreateInvite: 1,
    generalKickMembers: 2,
    generalBanMembers: 4,
    generalAdministrator: 8,
    generalManageChannels: 16,
    generalManageGuild: 32,
    generalChangeNickname: 67108864,
    generalManageNicknames: 134217728,
    generalManageRoles: 268435456,
    generalManageWebhooks: 536870912,
    generalManageEmojis: 1073741824,
    generalViewAuditLog: 128,
    generalViewGuildInsights: 524288,
    generalManageEvents: 8589934592,
    textAddReactions: 64,
    textSendMessages: 2048,
    textSendMessagesThreads: 274877906944,
    textCreatePublicThreads: 34359738368,
    textCreatePrivateThreads: 68719476736,
    textSendTTSMessages: 4096,
    textManageMessages: 8192,
    textManageThreads: 17179869184,
    textEmbedLinks: 16384,
    textAttachFiles: 32768,
    textReadMessageHistory: 65536,
    textMentionEveryone: 131072,
    textUseExternalEmojis: 262144,
    textUseExternalStickers: 137438953472,
    textUseSlashCommands: 2147483648,
    voiceConnect: 1048576,
    voiceSpeak: 2097152,
    voiceStream: 512,
    voiceMuteMembers: 4194304,
    voiceDeafenMembers: 8388608,
    voiceMoveMembers: 16777216,
    voiceUseVAD: 33554432,
    voiceStartActivities: 549755813888,
    voicePrioritySpeaker: 256,
    voiceStageRequestSpeak: 4294967296
};
  
let darkTheme = true;
  
function swapTheme() {
    darkTheme = !darkTheme;
    document.body.className = darkTheme ? "" : "light";
}
  
function recalculate(t, n) {
    t = t || 0;
    const a = [];
    for (const s in perms) {
      const checkbox = document.getElementById(s);
      if (s !== "voiceViewChannel" && checkbox.checked) {
        t += perms[s];
        a.push("0x" + perms[s].toString(16));
      }
    }


    let aString = " = " + a.join(" | ");
    document.getElementById("number").innerHTML = "" + t;
    document.getElementById("equation").innerHTML = t + aString;
    if (!n) {
      setHash("" + t);
    }

    const clientId = document.getElementById("clientID");
    const oauthScopes = document.getElementById("oauthScopes");
    const oauthCodeGrant = document.getElementById("oauthCodeGrant");
    const oauthRedirect = document.getElementById("oauthRedirect");
    const invite = document.getElementById("invite");
    if (clientId.value) {

      
    
      const o = clientId.value;
      if (o.match(/^\d{17,18}$/)) {
        clientId.className = "success";
        invite.className = "";
      } else {
        clientId.className = "error";
        invite.className = "disabled";
      }
      
      const i = oauthScopes.value;
      let c = "https://discord.com/oauth2/authorize?client_id=" + o + "&scope=" + (i ? encodeURIComponent(i.trim()) : "bot") + "&permissions=" + t;
      
      
      if (oauthCodeGrant.checked) {
        c += "&response_type=code";
      }
      if (oauthRedirect.value) {
        c += "&redirect_uri=" + encodeURIComponent(oauthRedirect.value);
      }
      invite.className = "";
      invite.innerHTML = invite.href = c;
    } else {
      clientId.className = "error";
      invite.className = "disabled";
      invite.innerHTML = "https://discord.com/oauth2/authorize?client_id=INSERT_CLIENT_ID_HERE&scope=bot&permissions=" + (t + "").split("=")[0].trim();
      invite.href = "#";
    }
}
  
function getHash(e) {
    e = e || window.location.hash;
    return e && e.length > 1 ? e.substring(1) : null;
}
  
function setHash(e) {
    if (history.pushState) {
      history.pushState(null, '', "#" + e);
    } else {
      window.location.hash = "#" + e;
    }
}
  
function syncCheckboxes(e){
    const t = Math.floor(e / 4294967296);
    const n = Math.floor(e % 4294967296);
    for (const a in oldPerms) {

      const aChecked = document.getElementById(a);

      if (
        (4294967296 <= oldPerms[a] && t & Math.floor(oldPerms[a] / 4294967296)) || 
        (oldPerms[a] < 4294967296 && n & oldPerms[a])
      ) {
        aChecked.checked = true;
      } else {
        aChecked.checked = false;
      }
    }
}
  
window.onpopstate = function (e) {
    const windowEvent = e.target;
    const hash = getHash(windowEvent.location.hash);
    if (hash !== null) {
        syncCheckboxes(+hash);
        recalculate(null, true);
    }
};
  
window.onhashchange = function (e) {
    const windowEvent = e.target;
    const hash = getHash(windowEvent.location.hash);
    if (hash !== null) {
        syncCheckboxes(+hash);
        recalculate(null, true);
    }
};
const oldHashGet = getHash()
if (oldHashGet !== null) {
    syncCheckboxes(+oldHashGet);
    recalculate(null, true);
}


function copyToClipboard(e,id) {
  // コピー対象をJavaScript上で変数として定義する
  const copyTarget = document.getElementById(id);

  let buttonElement = document.getElementById(e.id)

  //console.log(copyTarget.outerText)

  // コピー対象のテキストを選択する
  //if(copyTarget.outerText === undefined){return}

  // 選択しているテキストをクリップボードにコピーする
  navigator.clipboard.writeText(copyTarget.outerText)

  console.log(buttonElement.outerText)

  const copyText = buttonElement.textContent

  buttonElement.textContent = `コピーできました！`

  setTimeout(function() {
    //console.log(buttonElement.outerHTML);
    buttonElement.textContent = copyText
  }, 500);
  

  // コピーをお知らせする
  //alert("コピーできました！ : " + copyTarget.outerText);
}



