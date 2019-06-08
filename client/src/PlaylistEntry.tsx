import React from "react";
import {deleteTrackFromPlaylist, PlaylistItem, playTrackOfPlaylist} from "./api";
import {SortableHandle} from "react-sortable-hoc";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core";
import ListItem from "@material-ui/core/ListItem/ListItem";
import IconButton from "@material-ui/core/IconButton/IconButton";
import DragHandleRounded from '@material-ui/icons/DragHandleRounded';
import DeleteIcon from '@material-ui/icons/Delete';
import TrackListEntry from "./TrackListEntry";

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
    playlistIndex: number;
}

const DragHandleInstance = SortableHandle(() => <DragHandleRounded/>);


class PlaylistEntry extends React.Component<Props, {}> {

    swipeableViewsComponent: any;

    constructor(props: Props) {
        super(props);
        this.deleteTrackFromPlaylist = this.deleteTrackFromPlaylist.bind(this);
    }

    deleteTrackFromPlaylist(slidePosition: number): void {
        this.swipeableViewsComponent.setIndexCurrent(0);
        deleteTrackFromPlaylist(this.props.playlistItem.playlist_entry_id);
    }

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
                <SwipeableViews ref={(child: any) => {
                    this.swipeableViewsComponent = child;
                }} enableMouseEvents={true} onSwitching={(slidePosition: number, type: any) => {
                    if (slidePosition === 1.0) {
                        this.deleteTrackFromPlaylist(slidePosition)
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

            </div>
        );
    }
}

export default withStyles(styles)(PlaylistEntry);
