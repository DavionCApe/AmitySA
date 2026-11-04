from pathlib import Path
p=Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
s=p.read_text(encoding="utf-8")
for imp in ["import androidx.compose.animation.core.RepeatMode","import androidx.compose.animation.core.infiniteRepeatable","import androidx.compose.animation.core.rememberInfiniteTransition","import androidx.compose.animation.core.animateFloat","import android.content.Intent","import android.net.Uri"]:
    if imp not in s: s=s.replace("\nimport ","\n"+imp+"\nimport ",1)
s=s.replace("var showMenu by remember { mutableStateOf(false) }","var showMenu by remember { mutableStateOf(false) }\n    var showEmergency by remember { mutableStateOf(false) }",1)
old='''    } else {
        WelcomeScreen(account.username) { showMenu = true }
    }
}'''
new='''    } else if (showEmergency) {
        EmergencyServicesScreen(onPrevious = { showEmergency = false }, onNext = { showEmergency = false; showMenu = true })
    } else {
        WelcomeScreen(account.username) { showEmergency = true }
    }
}'''
if old not in s: raise SystemExit("Welcome screen transition not found")
s=s.replace(old,new,1)
s=s.replace('item { Header(account.username, onOpenThemes, onMenuAction) }', 'item { Header(account.username, onOpenThemes) { item -> if (item == "Home") showEmergency = false else onMenuAction(item) } }', 1)
s += r"""

private data class EmergencyContact(val category:String,val name:String,val number:String,val info:String,val icon:String)

@Composable
private fun EmergencyServicesScreen(onPrevious:()->Unit,onNext:()->Unit) {
    val t=LocalAmity.current
    val context=LocalContext.current
    val data=listOf(
      EmergencyContact("IMMEDIATE EMERGENCY","Mobile emergency services","112","Emergency response from a mobile phone","🚨"),
      EmergencyContact("POLICE & CRIME","SAPS emergency / Flying Squad","10111","South African Police Service","🚓"),
      EmergencyContact("POLICE & CRIME","Crime Stop","0860 010 111","Report crime-related information","🛡️"),
      EmergencyContact("MEDICAL & POISONING","Ambulance services","10177","National ambulance emergency number","🚑"),
      EmergencyContact("MEDICAL & POISONING","Poisons Information Helpline","0861 555 777","Poison exposure advice (Western Cape)","☣️"),
      EmergencyContact("FIRE & DISASTER","City of Cape Town emergency","107","Landline emergency line; mobile: 021 480 7700","🚒"),
      EmergencyContact("FIRE & DISASTER","Disaster Risk Management","080 911 4357","Western Cape disaster assistance","🔥"),
      EmergencyContact("CHILD & FAMILY SAFETY","Childline South Africa","116","Help and support for children","🧒"),
      EmergencyContact("CHILD & FAMILY SAFETY","GBV Command Centre","0800 428 428","24-hour support; USSD: *120*7867#","🤝"),
      EmergencyContact("CHILD & FAMILY SAFETY","Human Trafficking Helpline","0800 222 777","Report suspected human trafficking","🆘"),
      EmergencyContact("CRISIS & COUNSELLING","Lifeline","0861 322 322","Crisis counselling and emotional support","💚"),
      EmergencyContact("SEA & MOUNTAIN RESCUE","NSRI Sea Rescue","087 094 9774","National Sea Rescue Institute","🌊"),
      EmergencyContact("SEA & MOUNTAIN RESCUE","Wilderness Search & Rescue","021 937 0300","Search and rescue","⛰️")
    )
    val grouped=data.groupBy{it.category}
    val transition=rememberInfiniteTransition(label="navBounce")
    val dy by transition.animateFloat(0f,-7f, infiniteRepeatable(tween(500),RepeatMode.Reverse),label="bounce")
    Column(Modifier.fillMaxSize().background(t.canvas)) {
      Row(Modifier.fillMaxWidth().padding(14.dp),horizontalArrangement=Arrangement.SpaceBetween,verticalAlignment=Alignment.CenterVertically) {
        Button(onClick=onPrevious,modifier=Modifier.offset(y=dy.dp)){Text("‹ Previous")}
        Text("SAFETY DIRECTORY",color=t.primary,fontWeight=FontWeight.ExtraBold,fontSize=12.sp)
        Button(onClick=onNext,modifier=Modifier.offset(y=(-dy).dp)){Text("Next ›")}
      }
      Text("South African Emergency Services",Modifier.padding(horizontal=20.dp),color=t.ink,fontSize=23.sp,fontWeight=FontWeight.ExtraBold)
      Text("Tap a service card to open your phone dialler. Scroll to see all categories.",Modifier.padding(horizontal=20.dp,vertical=8.dp),color=t.inkSoft,fontSize=13.sp)
      LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(16.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
        grouped.forEach{(category,itemsForCategory)->
          item { Text(category,color=t.primary,fontSize=12.sp,fontWeight=FontWeight.ExtraBold,letterSpacing=1.sp) }
          items(itemsForCategory){ entry->
            var visible by remember{mutableStateOf(false)}
            LaunchedEffect(Unit){delay(90);visible=true}
            AnimatedVisibility(visible,enter=fadeIn(tween(300))+slideInVertically(initialOffsetY={it/4},animationSpec=tween(350))) {
              Card(Modifier.fillMaxWidth(),shape=RoundedCornerShape(20.dp),colors=CardDefaults.cardColors(containerColor=t.card),elevation=CardDefaults.cardElevation(4.dp)){
                Row(Modifier.fillMaxWidth().clickable{
                  val n=entry.number.filter{it.isDigit()||it=='+'}
                  context.startActivity(Intent(Intent.ACTION_DIAL,Uri.parse("tel:"+n)))
                }.padding(15.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(12.dp)){
                  Text(entry.icon,fontSize=26.sp)
                  Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(4.dp)){
                    Text(entry.name,color=t.ink,fontWeight=FontWeight.Bold,fontSize=15.sp)
                    Text(entry.info,color=t.inkSoft,fontSize=12.sp)
                    Text(entry.number,color=t.primary,fontWeight=FontWeight.ExtraBold,fontSize=17.sp)
                  }
                  Text("CALL",color=t.primary,fontWeight=FontWeight.Bold,fontSize=11.sp)
                }
              }
            }
          }
        }
        item{Text("Quick-reference contacts. If someone is in immediate danger, contact emergency services directly. Verify local numbers periodically.",Modifier.padding(8.dp),color=t.inkSoft,fontSize=11.sp)}
      }
    }
}
"""
p.write_text(s,encoding="utf-8")
print("Emergency directory inserted.")
