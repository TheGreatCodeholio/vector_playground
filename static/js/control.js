let movementState = 'stopped';
let liftState = 'lift-stopped';
let headState = 'head-stopped';

function sendControlRequests() {
  if (useKeyboardControl == true) {
    let newMovementState = getMovementState(keysPressed);
    if (newMovementState !== movementState) {
      sendMovementCommand(newMovementState);
      movementState = newMovementState;
    }

    let newLiftState = getLiftState(keysPressed);
    if (newLiftState !== liftState) {
      sendLiftCommand(newLiftState);
      liftState = newLiftState;
    }

    let newHeadState = getHeadState(keysPressed);
    if (newHeadState !== headState) {
      sendHeadCommand(newHeadState);
      headState = newHeadState;
    }
  }
}

function getMovementState(keysPressed) {
  const w = keysPressed['w'];
  const a = keysPressed['a'];
  const s = keysPressed['s'];
  const d = keysPressed['d'];

  if (!w && !a && !s && !d) {
    return 'stopped';
  }
  if (w && !s) {
    if (a && !d) return 'forward-left';
    if (!a && d) return 'forward-right';
    if (!a && !d) return 'forward';
  }
  if (s && !w) {
    if (a && !d) return 'backward-left';
    if (!a && d) return 'backward-right';
    if (!a && !d) return 'backward';
  }
  if (!w && !s) {
    if (a && !d) return 'left';
    if (!a && d) return 'right';
  }
  return 'stopped';
}

function sendMovementCommand(state) {
  switch (state) {
    case 'stopped':
      sendForm("/api-sdk/move_wheels?lw=0&rw=0");
      sendForm("/api-sdk/move_wheels?lw=0&rw=0");
      break;
    case 'forward':
      sendForm("/api-sdk/move_wheels?lw=140&rw=140");
      break;
    case 'forward-left':
      sendForm("/api-sdk/move_wheels?lw=100&rw=190");
      break;
    case 'forward-right':
      sendForm("/api-sdk/move_wheels?lw=190&rw=100");
      break;
    case 'left':
      sendForm("/api-sdk/move_wheels?lw=-150&rw=150");
      break;
    case 'right':
      sendForm("/api-sdk/move_wheels?lw=150&rw=-150");
      break;
    case 'backward':
      sendForm("/api-sdk/move_wheels?lw=-150&rw=-150");
      break;
    case 'backward-left':
      sendForm("/api-sdk/move_wheels?lw=-100&rw=190");
      break;
    case 'backward-right':
      sendForm("/api-sdk/move_wheels?lw=-190&rw=100");
      break;
  }
}

function getLiftState(keysPressed) {
  const r = keysPressed['r'];
  const f = keysPressed['f'];

  if (!r && !f) {
    return 'lift-stopped';
  }
  if (r && !f) {
    return 'lift-up';
  }
  if (!r && f) {
    return 'lift-down';
  }
  return 'lift-stopped';
}

function sendLiftCommand(state) {
  switch (state) {
    case 'lift-stopped':
      sendForm("/api-sdk/move_lift?speed=0");
      break;
    case 'lift-up':
      sendForm("/api-sdk/move_lift?speed=2");
      break;
    case 'lift-down':
      sendForm("/api-sdk/move_lift?speed=-2");
      break;
  }
}

function getHeadState(keysPressed) {
  const t = keysPressed['t'];
  const g = keysPressed['g'];

  if (!t && !g) {
    return 'head-stopped';
  }
  if (t && !g) {
    return 'head-up';
  }
  if (!t && g) {
    return 'head-down';
  }
  return 'head-stopped';
}

function sendHeadCommand(state) {
  switch (state) {
    case 'head-stopped':
      sendForm("/api-sdk/move_head?speed=0");
      break;
    case 'head-up':
      sendForm("/api-sdk/move_head?speed=2");
      break;
    case 'head-down':
      sendForm("/api-sdk/move_head?speed=-2");
      break;
  }
}
