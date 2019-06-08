import React from "react";
import {formatDuration, Track} from "./api";
import {createStyles, ListItemAvatar, Theme, WithStyles, withStyles} from "@material-ui/core";
import ListItem from "@material-ui/core/ListItem/ListItem";
import ListItemText from "@material-ui/core/ListItemText/ListItemText";
import classNames from 'classnames';
import PlayPauseButton from "./PlayPauseButton";


const styles = (theme: Theme) => createStyles({

    listItem: {
        paddingLeft: '4px',
        paddingRight: '4px',
    },
    currentEntry: {
        backgroundColor: theme.palette.primary.light
    },
    duration: {
        minWidth: '40px',
        textAlign: 'right',
        direction: 'rtl',
        paddingLeft: '0px',
        paddingRight: '8px',
    }
});


interface Props extends WithStyles<typeof styles> {
    track: Track;
    showAsCurrent: boolean;
    showAsPlaying: boolean;
    playPauseCallback: () => void;
    rightIcon: JSX.Element;
}

class TrackListEntry extends React.Component<Props, {}> {

    render() {
        const {classes} = this.props;

        let listItemClasses = classes.listItem;
        if (this.props.showAsCurrent) {
            listItemClasses = classNames(classes.listItem, classes.currentEntry)
        }
        return (
            <ListItem key={this.props.track.url} role={undefined} divider={true} className={listItemClasses} dense>
                <ListItemAvatar>
                    <PlayPauseButton track={this.props.track}
                                     onClick={this.props.playPauseCallback}
                                     showAsPlaying={this.props.showAsPlaying}/>
                </ListItemAvatar>
                <ListItemText primary={this.props.track.title} secondary={this.props.track.artist}/>
                <ListItemText className={classes.duration} primary={formatDuration(this.props.track.duration)}/>
                {this.props.rightIcon}
            </ListItem>
        );
    }
}

export default withStyles(styles)(TrackListEntry);
