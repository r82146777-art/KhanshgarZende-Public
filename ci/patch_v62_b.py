# layout btn
lx=(res/"layout"/"activity_settings.xml").read_text(encoding="utf-8")
if "btn_pick_apps" not in lx:
    ins='\n    <com.google.android.material.button.MaterialButton android:id="@+id/btn_pick_apps" style="@style/SecondaryButton" android:layout_width="match_parent" android:layout_height="wrap_content" android:text="انتخاب دستی برنامه‌ها برای خواندن با صدای بلند" />\n'
    m=re.search(r'(<androidx\.appcompat\.widget\.SwitchCompat\s+android:id="@\+id/sw_read_all_apps"[\s\S]*?/>)',lx)
    lx=(lx[:m.end()]+ins+lx[m.end():]) if m else lx.replace("</LinearLayout>\n</ScrollView>",ins+"\n</LinearLayout>\n</ScrollView>")
    (res/"layout"/"activity_settings.xml").write_text(lx,encoding="utf-8"); print("layout")

# Settings
sa=src/"SettingsActivity.kt"; sat=sa.read_text(encoding="utf-8")
sat=re.sub(r'private fun selectVoice\(key: String\)\s*\{[\s\S]*?\n    \}','private fun selectVoice(key:String){try{p.voice=key;try{app.speech.reloadVoice()}catch(e:Throwable){android.util.Log.e("S","rv",e)};try{updateBoxes()}catch(_:Throwable){}}catch(e:Throwable){android.util.Log.e("S","sv",e);toast("err")}}',sat,count=1)
sat=re.sub(r'private fun updateBoxes\(\)\s*\{[\s\S]*?\n    \}','private fun updateBoxes(){try{findViewById<View?>(R.id.system_box)?.visibility=if(p.voice=="system")View.VISIBLE else View.GONE;findViewById<View?>(R.id.azure_box)?.visibility=View.GONE;findViewById<View?>(R.id.btn_pick_apps)?.visibility=if(p.readAllApps)View.GONE else View.VISIBLE}catch(_:Throwable){}}',sat,count=1)
if "showAppPicker" not in sat:
    sat=re.sub(r'findViewById<SwitchCompat>\(R\.id\.sw_read_all_apps\)\?\.let\s*\{[\s\S]*?\n\s*\}',
        'findViewById<SwitchCompat>(R.id.sw_read_all_apps)?.let{sw->sw.isChecked=try{p.readAllApps}catch(_:Throwable){true};sw.setOnCheckedChangeListener{_,c->try{p.readAllApps=c;findViewById<View?>(R.id.btn_pick_apps)?.visibility=if(c)View.GONE else View.VISIBLE}catch(_:Throwable){}}};findViewById<View?>(R.id.btn_pick_apps)?.let{btn->btn.visibility=if(p.readAllApps)View.GONE else View.VISIBLE;btn.setOnClickListener{showAppPicker()}}',
        sat,count=1)
    sat=sat[:sat.rfind("}")]+r'''
    private fun showAppPicker(){
        try{
            val pm=packageManager
            val apps=pm.getInstalledApplications(0).filter{pm.getLaunchIntentForPackage(it.packageName)!=null}.sortedBy{it.loadLabel(pm).toString()}
            val labels=apps.map{it.loadLabel(pm).toString()+"\n"+it.packageName}.toTypedArray()
            val checked=BooleanArray(apps.size){i->p.allowedPackages.split(',','\n').map{it.trim()}.filter{it.isNotEmpty()}.contains(apps[i].packageName)}
            androidx.appcompat.app.AlertDialog.Builder(this).setTitle("برنامه‌ها").setMultiChoiceItems(labels,checked){_,w,c->checked[w]=c}
                .setPositiveButton("ذخیره"){_,_->val sel=apps.indices.filter{checked[it]}.map{apps[it].packageName};p.allowedPackages=sel.joinToString(",");p.readAllApps=false;findViewById<SwitchCompat?>(R.id.sw_read_all_apps)?.isChecked=false;findViewById<View?>(R.id.btn_pick_apps)?.visibility=View.VISIBLE;toast("${sel.size}")}
                .setNegativeButton("انصراف",null).show()
        }catch(e:Throwable){android.util.Log.e("S","pick",e)}
    }
}
'''
sa.write_text(sat,encoding="utf-8"); print("Settings")

# ReadAloud
(src/"ReadAloudService.kt").write_text(r'''package com.example.khanshgarzende
import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
class ReadAloudService:AccessibilityService(){
    companion object{private const val TAG="ReadAloud";@Volatile var instance:ReadAloudService?=null}
    private lateinit var prefs:Prefs; private var lastText=""; private var lastSpeakAt=0L
    override fun onServiceConnected(){super.onServiceConnected();instance=this;prefs=Prefs(this)
        serviceInfo=serviceInfo?.apply{eventTypes=AccessibilityEvent.TYPE_VIEW_CLICKED or AccessibilityEvent.TYPE_VIEW_FOCUSED or AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED or AccessibilityEvent.TYPE_VIEW_TEXT_SELECTION_CHANGED
            feedbackType=AccessibilityServiceInfo.FEEDBACK_SPOKEN;flags=flags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;notificationTimeout=100}}
    override fun onAccessibilityEvent(event:AccessibilityEvent?){if(event==null)return
        try{val pkg=event.packageName?.toString()?:return;if(pkg==packageName)return;if(!prefs.isPackageAllowed(pkg))return
            val text=extract(event);if(text.isBlank()||text==lastText)return;val now=System.currentTimeMillis();if(now-lastSpeakAt<700)return
            lastText=text;lastSpeakAt=now;speak(text)}catch(e:Throwable){Log.e(TAG,"e",e)}}
    private fun extract(event:AccessibilityEvent):String{val sb=StringBuilder();event.text?.forEach{if(!it.isNullOrBlank())sb.append(it).append(' ')}
        if(sb.isBlank())event.source?.let{n->collect(n,sb,0);try{n.recycle()}catch(_:Throwable){}};return sb.toString().trim().take(800)}
    private fun collect(node:AccessibilityNodeInfo?,sb:StringBuilder,depth:Int){if(node==null||depth>6||sb.length>800)return
        val t=node.text?.toString();if(!t.isNullOrBlank())sb.append(t).append(' ');val d=node.contentDescription?.toString();if(!d.isNullOrBlank()&&d!=t)sb.append(d).append(' ')
        for(i in 0 until node.childCount){val c=node.getChild(i)?:continue;collect(c,sb,depth+1);try{c.recycle()}catch(_:Throwable){}}}
    private fun speak(text:String){try{val app=application as? App?:return;app.speech.stop();app.speech.speak(text)}catch(e:Throwable){Log.e(TAG,"s",e)}}
    override fun onInterrupt(){try{(application as? App)?.speech?.stop()}catch(_:Throwable){}}
    override fun onDestroy(){instance=null;super.onDestroy()}
}
''',encoding="utf-8")
(res/"xml").mkdir(parents=True,exist_ok=True)
(res/"xml"/"readaloud_service.xml").write_text('<?xml version="1.0" encoding="utf-8"?>\n<accessibility-service xmlns:android="http://schemas.android.com/apk/res/android" android:accessibilityEventTypes="typeViewClicked|typeViewFocused|typeWindowStateChanged|typeViewTextSelectionChanged" android:accessibilityFeedbackType="feedbackSpoken" android:notificationTimeout="100" android:canRetrieveWindowContent="true" android:settingsActivity="com.example.khanshgarzende.SettingsActivity" android:description="@string/readaloud_description" android:accessibilityFlags="flagReportViewIds|flagRetrieveInteractiveWindows" />\n',encoding="utf-8")
sx=res/"values"/"strings.xml"
if sx.exists():
    s=sx.read_text(encoding="utf-8")
    if "readaloud_description" not in s: sx.write_text(s.replace("</resources>",'    <string name="readaloud_description">خواندن با صدای بلند</string>\n</resources>'),encoding="utf-8")
else:
    (res/"values").mkdir(parents=True,exist_ok=True)
    sx.write_text('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <string name="app_name">خوانشگر زنده</string>\n    <string name="readaloud_description">خواندن با صدای بلند</string>\n</resources>\n',encoding="utf-8")
mp=proj/"app/src/main/AndroidManifest.xml"; man=mp.read_text(encoding="utf-8")
if "ReadAloudService" not in man:
    man=man.replace("</application>",'''
        <service android:name=".ReadAloudService" android:exported="true" android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">
            <intent-filter><action android:name="android.accessibilityservice.AccessibilityService" /></intent-filter>
            <meta-data android:name="android.accessibilityservice" android:resource="@xml/readaloud_service" />
        </service>
    </application>''')
if "<queries>" not in man:
    man=man.replace("<application",'''<queries><intent><action android:name="android.intent.action.MAIN" /><category android:name="android.intent.category.LAUNCHER" /></intent></queries>
    <application''',1)
mp.write_text(man,encoding="utf-8"); print("ReadAloud")
bg=proj/"app/build.gradle.kts"; bt=bg.read_text(encoding="utf-8")
bt=re.sub(r"versionCode\s*=\s*\d+","versionCode = 62",bt)
bt=re.sub(r'versionName\s*=\s*"[^"]*"','versionName = "6.2"',bt)
bg.write_text(bt,encoding="utf-8"); print("DONE",sa.read_text().count("{"),sa.read_text().count("}"))
