import React from "react";
import {Track} from "./api";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core";
import IconButton from "@material-ui/core/IconButton/IconButton";
import PlayArrow from '@material-ui/icons/PlayArrowRounded';
import Pause from '@material-ui/icons/PauseRounded';
import Avatar from '@material-ui/core/Avatar';


const styles = (theme: Theme) => createStyles({

    avatar: {
        position: 'absolute',
        width: '44px',
        height: '44px'
    },
    playPauseButton: {
        zIndex: 50
    },
    icon: {
        backgroundColor: 'white',
        borderRadius: '50%',
    }
});


interface Props extends WithStyles<typeof styles> {
    track: Track;
    onClick: () => void;
    showAsPlaying: boolean;
}



class PlayPauseButton extends React.Component<Props, {}> {

    render() {
        const {classes} = this.props;

        const actionIcon = this.props.showAsPlaying ?
            <Pause fontSize={"small"} className={classes.icon}/> :
            <PlayArrow fontSize={"small"} className={classes.icon}/>;

        return (
            <div>
                <Avatar src={this.props.track.cover_url} className={classes.avatar}/>
                <IconButton color="secondary" onClick={this.props.onClick} className={classes.playPauseButton}>
                    {actionIcon}
                </IconButton>
            </div>
        );
    }
}



export default withStyles(styles)(PlayPauseButton);
