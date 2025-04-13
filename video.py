from slideMaker.agent import createScriptAndAnimations


def generateAndSaveVideo(videoInfo, voiceId, background):
    # Send request with function declarations

    # Generate Script for audio and HTML for animations
    slidesDir, scriptPath = createScriptAndAnimations(videoInfo)

    animationDir =  generateAnimationAsMp4(slidesDir)
    audioDir = generateAudioAsMP3(scriptPath, voiceId)
    characterMotionDir = generateCharacterMotionAsMp4(audioDir)

    # Combine the video (slides of character, animations and audio stiched together) to a file
    finalVideoPath = combineAudioAndAnimationAndOverlayBackground(animationDir, audioDir, characterMotionDir, background)
    
    return finalVideoPath

def generateAudioAsMP3(scriptPath, voiceId):
    pass

def generateAnimationAsMp4(slidesDir):
    pass

def combineAudioAndAnimationAndOverlayBackground(animationDir, audioDir, characterMotionDir, background):
    pass


def generateCharacterMotionAsMp4(audioDir):
    pass