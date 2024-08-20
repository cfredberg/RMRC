let keys_down = {};
const motor_keys = ["w", "a", "s", "d"];

let left_tread_power_percent = 0;
let right_tread_power_percent = 0;

function init_script(){
    for (key of motor_keys){
        keys_down[key] = false;
    }

    console.log("Initilized Keys Down: " + JSON.stringify(keys_down));
}

function calculate_power(){

}

function keydown(e){
    console.log("Key Down");
    let key = e.key.toLowerCase();
    keys_down[key] = true;

    if (motor_keys.includes(key)){
        calculate_power();
    }

    document.getElementById("keys").innerHTML = JSON.stringify(keys_down);
}

function keyup(e){
    console.log("Key Up");
    let key = e.key.toLowerCase();
    keys_down[key] = false;

    if (motor_keys.includes(key)){
        calculate_power();
    }

    document.getElementById("keys").innerHTML = JSON.stringify(keys_down);
}


window.addEventListener("keydown", keydown);
window.addEventListener("keyup", keyup);