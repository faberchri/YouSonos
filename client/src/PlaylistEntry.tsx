import React from "react";
import {PlaylistItem, playTrackOfPlaylist} from "./api";
import {SortableHandle} from "react-sortable-hoc";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core";
import ListItem from "@material-ui/core/ListItem/ListItem";
import IconButton from "@material-ui/core/IconButton/IconButton";
import DragHandleRounded from '@material-ui/icons/DragHandleRounded';
import DeleteIcon from '@material-ui/icons/Delete';
import TrackListEntry from "./TrackListEntry";
import { PlaylistContext } from "./Playlist";

var SwipeableViews = require('react-swipeable-views').default;


const styles = (theme: Theme) => createStyles({
    root: {},
    deleteSlide: {
        height: '100%',
    },
    deleteListItem: {
        backgroundColor: theme.palette.error.main,
        height: '100%',
    },
    deleteButton: {
        float: 'right',
    }
});


interface Props extends WithStyles<typeof styles> {
    playlistItem: PlaylistItem;
}

const DragHandleInstance = SortableHandle(() => <DragHandleRounded/>);


class PlaylistEntry extends React.Component<Props, {}> {

    swipeableViewsComponent: any;

    render() {
        const {classes} = this.props;

        let showAsPlaying = false;
        if (this.props.playlistItem.status === 'CURRENT') {
            const trackStatus = this.props.playlistItem.track.track_status;
            if (trackStatus === 'PLAYING') {
                showAsPlaying = true;
            }
        }

        // additional <div> fixes error 'undefined is not an object (evaluating 'edgeOffset.top')' react-sortbale-hoc
        // https://github.com/clauderic/react-sortable-hoc/issues/305
        return (
            <div className={classes.root}>
                <PlaylistContext.Consumer>
                    {playlistContext => (
                    <SwipeableViews ref={(child: any) => {
                        this.swipeableViewsComponent = child;
                    }} enableMouseEvents={true} onSwitching={(slidePosition: number, type: any) => {
                        if (slidePosition === 1.0) {                        
                            playlistContext.onDelete(this.props.playlistItem.playlist_entry_id)
                            this.swipeableViewsComponent.setIndexCurrent(0);
                        }
                        }}>
                        <div>
                            <TrackListEntry showAsPlaying={showAsPlaying}
                                        track={this.props.playlistItem.track}
                                        rightIcon={<DragHandleInstance/>}
                                        playPauseCallback={() => playTrackOfPlaylist(this.props.playlistItem.playlist_entry_id)}
                                        showAsCurrent={this.props.playlistItem.status === 'CURRENT'}/>
                        </div>
                        <div className={classes.deleteSlide}>
                            <ListItem className={classes.deleteListItem} key={this.props.playlistItem.track.url}
                                        role={undefined} divider={true} dense>
                                <div className={classes.deleteButton}>
                                    <IconButton aria-label="Delete">
                                        <DeleteIcon fontSize={"small"}/>
                                    </IconButton>
                                </div>
                            </ListItem>
                        </div>
                    </SwipeableViews>
                    )}
                </PlaylistContext.Consumer>
            </div>
        );
    }
}

export default withStyles(styles)(PlaylistEntry);
